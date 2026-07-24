"""Validate the .analysis.hocon load-case vocabulary into normalized constraint/load/step dicts.

Pure functions (no kernel, no gmsh): each raises AnalysisParamError on a contract violation,
which the document layer wraps into a structured diagnostic (the loft_params -> op pattern).
The normalized dicts feed DeckWriter, so the CalculiX DOF convention is applied here once:
1-3 translations, 4-6 rotations, 11 temperature.
"""

import logging

logger = logging.getLogger(__name__)

_CONSTRAINT_TYPES = {"encastre": [1, 2, 3, 4, 5, 6], "pinned": [1, 2, 3]}
_VALID_DOF = frozenset({1, 2, 3, 4, 5, 6, 11})


class AnalysisParamError(Exception):
    """A constraint, load, or step in an analysis document violates the load-case vocabulary."""


def validate_constraint(constraint: dict) -> dict:
    """Normalize one boundary condition to ``{name, where, dof, value}``.

    ``type`` (encastre/pinned) expands to a fixed dof set; an explicit ``dof`` list overrides.
    :raises AnalysisParamError: on a missing name/where, unknown type, or out-of-range dof.
    """
    name = constraint.get("name")
    if not name:
        raise AnalysisParamError("constraint needs a 'name'")
    where = constraint.get("where")
    if not isinstance(where, dict) or not where:
        raise AnalysisParamError(f"constraint {name!r} needs a 'where' selector")
    dof = _constraint_dof(constraint, str(name))
    return {"name": str(name), "where": dict(where), "dof": dof,
            "value": float(constraint.get("value", 0.0))}


def _constraint_dof(constraint: dict, name: str) -> list[int]:
    """The fixed degrees of freedom for a constraint: explicit ``dof`` or a ``type`` keyword."""
    if "dof" in constraint:
        dof = [int(d) for d in constraint["dof"]]
        bad = [d for d in dof if d not in _VALID_DOF]
        if bad:
            raise AnalysisParamError(
                f"constraint {name!r} has out-of-range dof {bad}; valid: {sorted(_VALID_DOF)}")
        return dof
    ctype = str(constraint.get("type", ""))
    if ctype not in _CONSTRAINT_TYPES:
        raise AnalysisParamError(
            f"constraint {name!r} needs 'type' ({sorted(_CONSTRAINT_TYPES)}) or an explicit 'dof'")
    return list(_CONSTRAINT_TYPES[ctype])


# type -> the extra required field(s) beyond name/where. gravity is special (no where).
_LOAD_REQUIRED = {
    "force": ("vector",),
    "pressure": ("magnitude",),
    "flux": ("magnitude",),
    "film": ("sink", "coefficient"),
    "radiation": ("ambient", "emissivity"),
    "temperature": ("value",),
}


def validate_load(load: dict) -> dict:
    """Normalize one load to a typed dict carrying exactly the fields its CalculiX card needs.

    Structural: force (*CLOAD), pressure (*DLOAD), gravity (*DLOAD GRAV). Thermal: flux
    (*DFLUX), film (*FILM), radiation (*RADIATE), temperature (*BOUNDARY dof 11). Every type
    except gravity requires a ``where`` selector; gravity is a body force over the whole part.
    :raises AnalysisParamError: on a missing name, missing where (non-gravity), unknown type,
        or a missing type-specific field.
    """
    name = load.get("name")
    if not name:
        raise AnalysisParamError("load needs a 'name'")
    ltype = str(load.get("type", ""))
    if ltype == "gravity":
        return _validate_gravity(load, str(name))
    if ltype not in _LOAD_REQUIRED:
        raise AnalysisParamError(
            f"load {name!r} has unknown type {ltype!r}; valid: "
            f"{sorted(('gravity', *_LOAD_REQUIRED))}")
    where = load.get("where")
    if not isinstance(where, dict) or not where:
        raise AnalysisParamError(f"load {name!r} ({ltype}) needs a 'where' selector")
    result: dict = {"name": str(name), "type": ltype, "where": dict(where)}
    for field in _LOAD_REQUIRED[ltype]:
        if field not in load:
            raise AnalysisParamError(f"load {name!r} ({ltype}) needs '{field}'")
        result[field] = _coerce_load_field(field, load[field])
    return result


def _validate_gravity(load: dict, name: str) -> dict:
    """Normalize a gravity body force to ``{name, type, g, direction}`` (no where)."""
    if "g" not in load or "direction" not in load:
        raise AnalysisParamError(f"gravity load {name!r} needs 'g' and 'direction'")
    direction = [float(v) for v in load["direction"]]
    if len(direction) != 3:
        raise AnalysisParamError(f"gravity load {name!r} 'direction' must be [x, y, z]")
    return {"name": name, "type": "gravity", "g": float(load["g"]), "direction": direction}


def _coerce_load_field(field: str, value: object) -> float | list[float]:
    """Coerce a load field: ``vector``/``direction`` -> a 3-float list, any other field -> float."""
    if field in ("vector", "direction"):
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise AnalysisParamError(f"'{field}' must be [x, y, z]")
        return [float(v) for v in value]
    if not isinstance(value, (int, float)):
        raise AnalysisParamError(f"'{field}' must be a number; got {value!r}")
    return float(value)


_PROCEDURES = frozenset({"static", "frequency", "heat_transfer", "fatigue"})
_THERMAL_LOAD_TYPES = frozenset({"flux", "film", "radiation", "temperature"})
_DEFAULT_OUTPUT = {"node": ["U", "RF"], "element": ["S", "E"]}


def validate_step(step: dict) -> dict:
    """Normalize one analysis step (a CalculiX *STEP) by procedure.

    static -> *STATIC (+ optional nlgeom, field output); frequency -> *FREQUENCY (needs
    eigenvalues); heat_transfer -> *HEAT TRANSFER (default steady; nested loads must be thermal).
    :raises AnalysisParamError: on a missing name, unknown procedure, missing eigenvalues, or a
        non-thermal load nested in a heat_transfer step.
    """
    name = step.get("name")
    if not name:
        raise AnalysisParamError("step needs a 'name'")
    procedure = str(step.get("procedure", ""))
    if procedure not in _PROCEDURES:
        raise AnalysisParamError(
            f"step {name!r} has unknown procedure {procedure!r}; valid: {sorted(_PROCEDURES)}")
    if procedure == "static":
        return _validate_static(step, str(name))
    if procedure == "frequency":
        return _validate_frequency(step, str(name))
    if procedure == "fatigue":
        return _validate_fatigue(step, str(name))
    return _validate_heat_transfer(step, str(name))


def _validate_static(step: dict, name: str) -> dict:
    """A *STATIC step: optional geometric nonlinearity + requested field output."""
    output = step.get("output") or _DEFAULT_OUTPUT
    return {"name": name, "procedure": "static", "nlgeom": bool(step.get("nlgeom", False)),
            "output": {"node": list(output.get("node", _DEFAULT_OUTPUT["node"])),
                       "element": list(output.get("element", _DEFAULT_OUTPUT["element"]))}}


def _validate_frequency(step: dict, name: str) -> dict:
    """A *FREQUENCY step: extract ``eigenvalues`` (mode count), which must be a positive int."""
    if "eigenvalues" not in step:
        raise AnalysisParamError(f"frequency step {name!r} needs 'eigenvalues' (mode count)")
    count = int(step["eigenvalues"])
    if count < 1:
        raise AnalysisParamError(f"frequency step {name!r} 'eigenvalues' must be >= 1")
    return {"name": name, "procedure": "frequency", "eigenvalues": count}


def _validate_fatigue(step: dict, name: str) -> dict:
    """A fatigue post-process: references a static step ``of`` + a stress ratio ``ratio``.

    Not a CalculiX step (see AnalysisDocument); it post-processes the referenced static step's
    solved peak stress. :raises AnalysisParamError: on a missing ``of`` or a ratio outside [-1, 1).
    """
    of = step.get("of")
    if not of:
        raise AnalysisParamError(f"fatigue step {name!r} needs 'of' (a static step name)")
    ratio = float(step.get("ratio", -1.0))
    if not (-1.0 <= ratio < 1.0):
        raise AnalysisParamError(
            f"fatigue step {name!r} 'ratio' must be in [-1, 1); got {ratio}")
    return {"name": name, "procedure": "fatigue", "of": str(of), "ratio": ratio}


def _validate_heat_transfer(step: dict, name: str) -> dict:
    """A *HEAT TRANSFER step: state (default steady) + nested thermal-only loads."""
    loads = []
    for load in step.get("loads", []) or []:
        normalized = validate_load(load)
        if normalized["type"] not in _THERMAL_LOAD_TYPES:
            raise AnalysisParamError(
                f"heat_transfer step {name!r} load {normalized['name']!r} is "
                f"{normalized['type']!r}; only thermal loads {sorted(_THERMAL_LOAD_TYPES)} allowed")
        loads.append(normalized)
    return {"name": name, "procedure": "heat_transfer",
            "state": str(step.get("state", "steady")), "loads": loads}
