"""Parse a ``.analysis.hocon`` load case: the structural-FEA semantics over a built part.

An analysis document references a PART (which supplies the geometry to mesh) and declares the
load case: boundary conditions (constraints), loads, and steps. This mirrors how a
``.physics.hocon`` overlays an assembly. An ncad load case = a CalculiX *STEP; the vocabulary
maps 1:1 to real .inp cards (see DeckWriter). This class validates the document into a
queryable spec; geometry and material properties are never authored here.

Document shape::

    analysis {
      part = bracket.hocon
      mesh { element_size = 3.0, order = 2 }
      constraints = [ { name = root, where = {face=bottom}, type = encastre } ]
      loads = [ { name = tip, where = {face=top}, type = pressure, magnitude = 2.5e5 } ]
      steps = [ { name = stress, procedure = static } ]
    }
"""

from ncad.fea.analysis_params import validate_constraint, validate_load, validate_step

_DEFAULT_ORDER = 2
_DEFAULT_ELEMENT_SIZE = 5.0
_DEFAULT_MIN_QUALITY = 0.0


class AnalysisSpecError(Exception):
    """An analysis document is missing its 'analysis' block or its 'part' reference."""


class AnalysisSpec:
    """A validated ``.analysis.hocon`` load case: part ref, mesh opts, constraints, loads, steps."""

    def __init__(self, document: dict) -> None:
        analysis = document.get("analysis")
        if not isinstance(analysis, dict):
            raise AnalysisSpecError("analysis document needs a top-level 'analysis' block")
        if not analysis.get("part"):
            raise AnalysisSpecError("analysis load case needs a 'part' reference")
        self._part = str(analysis["part"])
        self._mesh = _mesh_options(analysis.get("mesh") or {})
        self._constraints = [validate_constraint(c) for c in analysis.get("constraints", [])]
        self._loads = [validate_load(load) for load in analysis.get("loads", [])]
        self._steps = [validate_step(s) for s in analysis.get("steps", [])]
        self._material_override = analysis.get("material")

    @property
    def part(self) -> str:
        """The referenced part document path (relative to the analysis doc)."""
        return self._part

    @property
    def mesh(self) -> dict:
        """Mesh options ``{element_size, order, min_quality}`` (defaults applied)."""
        return dict(self._mesh)

    @property
    def constraints(self) -> list[dict]:
        """Normalized boundary conditions (each ``{name, where, dof, value}``)."""
        return [dict(c) for c in self._constraints]

    @property
    def loads(self) -> list[dict]:
        """Normalized top-level (structural) loads."""
        return [dict(load) for load in self._loads]

    @property
    def steps(self) -> list[dict]:
        """Normalized steps, in authored order (each a CalculiX *STEP)."""
        return [dict(s) for s in self._steps]

    @property
    def material_override(self) -> dict | None:
        """An optional material property override deep-merged over the part's material, or None."""
        return dict(self._material_override) if isinstance(self._material_override, dict) else None


def _mesh_options(mesh: dict) -> dict:
    """Apply mesh-option defaults: quadratic tets, a coarse default size, no quality floor."""
    return {
        "element_size": float(mesh.get("element_size", _DEFAULT_ELEMENT_SIZE)),
        "order": int(mesh.get("order", _DEFAULT_ORDER)),
        "min_quality": float(mesh.get("min_quality", _DEFAULT_MIN_QUALITY)),
    }
