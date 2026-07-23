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
