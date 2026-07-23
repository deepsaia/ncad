"""Compose a complete CalculiX .inp deck from a meshed .inp plus the analysis load case.

The mesh .inp (from GmshMesher) already carries the nodes, C3D4/C3D10 elements, and one named
NSET/ELSET per constraint/load. DeckWriter APPENDS the material, solid section, and one *STEP per
analysis step. Pure: same (mesh text, spec, material) -> same deck string. An ncad load case = a
CalculiX *STEP; every card here maps 1:1 to the manual (verified against the CalculiX-Examples
decks). Standard DOF convention: 1-3 translations, 4-6 rotations, 11 temperature.
"""

import logging

from ncad.fea.analysis_error import AnalysisError

logger = logging.getLogger(__name__)

_MATERIAL_NAME = "ncad_material"
# Which structural dofs a force component drives: vector index 0/1/2 -> CalculiX dof 1/2/3.
_FORCE_DOF = (1, 2, 3)


class DeckWriter:
    """Builds a complete CalculiX .inp deck from a meshed .inp and an AnalysisSpec load case."""

    def write(self, mesh_inp_text: str, spec, material: dict, element_set: str = "all") -> str:
        """Return the full deck: the mesh .inp with material + section + steps appended.

        :param spec: an AnalysisSpec (part, constraints, loads, steps).
        :param material: a resolved mat_data dict (structural/physical/thermal groups).
        :param element_set: the volume ELSET name GmshMesher wrote (default ``all``).
        :raises AnalysisError: if a heat_transfer step is present but the material has no
            thermal.conductivity (the load case needs a property the material does not carry).
        """
        needs_thermal = any(s["procedure"] == "heat_transfer" for s in spec.steps)
        blocks = [mesh_inp_text.rstrip(),
                  _material_block(material, needs_thermal),
                  _section_block(element_set),
                  *[_step_block(step, spec, element_set) for step in spec.steps]]
        return "\n".join(blocks) + "\n"


def _material_block(material: dict, needs_thermal: bool) -> str:
    """The *MATERIAL block: elastic (E, nu) + density (+ conductivity for a thermal step)."""
    structural = material.get("structural") or {}
    youngs = structural.get("youngs_modulus")
    poisson = structural.get("poisson")
    if youngs is None or poisson is None:
        raise AnalysisError("material needs structural.youngs_modulus and structural.poisson")
    density = (material.get("physical") or {}).get("density", 0.0)
    lines = [f"*MATERIAL, NAME={_MATERIAL_NAME}",
             "*ELASTIC", f"{youngs:.6g}, {poisson:.6g}",
             "*DENSITY", f"{density:.6g}"]
    if needs_thermal:
        conductivity = (material.get("thermal") or {}).get("conductivity")
        if conductivity is None:
            raise AnalysisError(
                "a heat_transfer step needs material thermal.conductivity, which is not set")
        lines += ["*CONDUCTIVITY", f"{conductivity:.6g}"]
    return "\n".join(lines)


def _section_block(element_set: str) -> str:
    """The *SOLID SECTION binding the whole volume element set to the material."""
    return f"*SOLID SECTION, ELSET={element_set}, MATERIAL={_MATERIAL_NAME}"


def _step_block(step: dict, spec, element_set: str) -> str:
    """One CalculiX *STEP for an analysis step, dispatched by procedure."""
    procedure = step["procedure"]
    if procedure == "static":
        return _static_step(step, spec, element_set)
    if procedure == "frequency":
        return _frequency_step(step, spec)
    return _heat_transfer_step(step, spec)


def _static_step(step: dict, spec, element_set: str) -> str:
    """A *STATIC step: fixed BCs + structural loads -> displacement + stress output."""
    nlgeom = ", NLGEOM" if step.get("nlgeom") else ""
    output = step.get("output") or {"node": ["U", "RF"], "element": ["S", "E"]}
    lines = [f"*STEP{nlgeom}", "*STATIC",
             _boundary_block(spec.constraints),
             *[_load_card(load, element_set) for load in spec.loads],
             "*NODE FILE", ", ".join(output.get("node", ["U"])),
             "*EL FILE", ", ".join(output.get("element", ["S"])),
             "*END STEP"]
    return "\n".join(x for x in lines if x)


def _frequency_step(step: dict, spec) -> str:
    """A *FREQUENCY step: extract the first ``eigenvalues`` natural modes."""
    lines = ["*STEP", "*FREQUENCY", f"{step['eigenvalues']}",
             _boundary_block(spec.constraints),
             "*NODE FILE", "U", "*END STEP"]
    return "\n".join(x for x in lines if x)


def _heat_transfer_step(step: dict, spec) -> str:
    """A *HEAT TRANSFER, STEADY STATE step: the step's thermal loads -> a temperature field."""
    lines = ["*STEP", "*HEAT TRANSFER, STEADY STATE",
             _boundary_block(spec.constraints),
             *[_thermal_load_card(load) for load in step.get("loads", [])],
             "*NODE FILE", "NT", "*END STEP"]
    return "\n".join(x for x in lines if x)


def _boundary_block(constraints: list[dict]) -> str:
    """One *BOUNDARY block: each constraint fixes its dof range on its named node set."""
    if not constraints:
        return ""
    lines = ["*BOUNDARY"]
    for constraint in constraints:
        dof = constraint["dof"]
        value = constraint["value"]
        # Contiguous dof runs collapse to a "first, last" line; otherwise one line per dof.
        for start, end in _contiguous_runs(dof):
            lines.append(f"{constraint['name']}, {start}, {end}, {value:.6g}")
    return "\n".join(lines)


def _load_card(load: dict, element_set: str) -> str:
    """A structural load card: force (*CLOAD), pressure (*DLOAD P), or gravity (*DLOAD GRAV).

    Pressure is applied over the load's named surface element set (GmshMesher writes one ELSET per
    load, named after the load); gravity is a body force over the whole volume element set.
    """
    ltype = load["type"]
    if ltype == "force":
        return _cload_card(load)
    if ltype == "pressure":
        # A uniform pressure over the load's named surface element set (CalculiX *DLOAD label P).
        return f"*DLOAD\n{load['name']}, P, {load['magnitude']:.6g}"
    if ltype == "gravity":
        dx, dy, dz = load["direction"]
        return (f"*DLOAD\n{element_set}, GRAV, {load['g']:.6g}, "
                f"{dx:.6g}, {dy:.6g}, {dz:.6g}")
    return ""


def _cload_card(load: dict) -> str:
    """A *CLOAD: split the force vector into one concentrated-load line per nonzero component."""
    lines = ["*CLOAD"]
    for index, component in enumerate(load["vector"]):
        if component != 0.0:
            lines.append(f"{load['name']}, {_FORCE_DOF[index]}, {component:.6g}")
    return "\n".join(lines)


def _thermal_load_card(load: dict) -> str:
    """A thermal load card: flux (*DFLUX), film (*FILM), radiation (*RADIATE), temp (*BOUNDARY)."""
    ltype = load["type"]
    name = load["name"]
    if ltype == "flux":
        return f"*DFLUX\n{name}, S, {load['magnitude']:.6g}"
    if ltype == "film":
        return f"*FILM\n{name}, F, {load['sink']:.6g}, {load['coefficient']:.6g}"
    if ltype == "radiation":
        return f"*RADIATE\n{name}, R, {load['ambient']:.6g}, {load['emissivity']:.6g}"
    if ltype == "temperature":
        return f"*BOUNDARY\n{name}, 11, 11, {load['value']:.6g}"
    return ""


def _contiguous_runs(dof: list[int]) -> list[tuple[int, int]]:
    """Collapse a sorted dof list into (first, last) contiguous runs for compact *BOUNDARY lines."""
    if not dof:
        return []
    ordered = sorted(set(dof))
    runs = []
    start = prev = ordered[0]
    for value in ordered[1:]:
        if value == prev + 1:
            prev = value
            continue
        runs.append((start, prev))
        start = prev = value
    runs.append((start, prev))
    return runs
