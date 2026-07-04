"""py-slvs (SolveSpace) implementation of the SketchSolver seam (design section 5).

Maps our 2D entities/constraints onto a SolveSpace System with a fixed base workplane
(group 1) and the sketch entities in the solved group (group 2), runs the solver, and
reads back solved point coordinates. GPL, per the settled solver-licensing decision
(design section 8). Entities/constraints reference each other by our string ids; a
dangling reference is reported as an id-tagged error before the solver runs.
"""

import logging
from typing import Any

from py_slvs import slvs

from ncad.ops.build_issue import BuildIssue
from ncad.sketch.sketch_solver import SketchSolver
from ncad.sketch.solve_result import SolveResult

logger = logging.getLogger(__name__)

_BASE_GROUP = 1
_SKETCH_GROUP = 2


class SlvsSolver(SketchSolver):
    """Solves sketches with SolveSpace via py-slvs."""

    def solve(self, entities: list[dict], constraints: list[dict],
              feature_id: str) -> SolveResult:
        by_id = {e["id"]: e for e in entities}
        missing = _missing_reference(entities, constraints, by_id)
        if missing is not None:
            return SolveResult(positions={}, dof=0, status="inconsistent",
                               issues=[BuildIssue(node_id=feature_id, message=missing)])
        system = slvs.System()
        origin = system.addPoint3dV(0.0, 0.0, 0.0, group=_BASE_GROUP)
        normal = system.addNormal3dV(1.0, 0.0, 0.0, 0.0, group=_BASE_GROUP)
        workplane = system.addWorkplane(origin, normal, group=_BASE_GROUP)

        point_handles: dict[str, Any] = {}
        line_handles: dict[str, Any] = {}
        for entity in entities:
            if entity["type"] == "point":
                u, v = entity["at"]
                point_handles[entity["id"]] = system.addPoint2dV(
                    workplane, float(u), float(v), group=_SKETCH_GROUP)
        for entity in entities:
            if entity["type"] == "line":
                line_handles[entity["id"]] = system.addLineSegment(
                    point_handles[entity["p1"]], point_handles[entity["p2"]],
                    group=_SKETCH_GROUP)

        for constraint in constraints:
            _add_constraint(system, constraint, workplane, point_handles, line_handles)

        code = system.solve(group=_SKETCH_GROUP, reportFailed=True)
        dof = int(system.Dof)
        failed = list(system.Failed)
        positions = {
            pid: (system.getParam(system.getEntityParam(handle, 0)).val,
                  system.getParam(system.getEntityParam(handle, 1)).val)
            for pid, handle in point_handles.items()
        }
        return _result_from(code, dof, failed, positions, feature_id)


def _missing_reference(entities: list[dict], constraints: list[dict],
                       by_id: dict[str, dict]) -> str | None:
    """The first dangling entity reference, as an error message, or None."""
    for entity in entities:
        if entity.get("type") == "line":
            for key in ("p1", "p2"):
                if entity.get(key) not in by_id:
                    return (f"line {entity.get('id')!r} references unknown point "
                            f"{entity.get(key)!r}")
    for constraint in constraints:
        for ref in _constraint_refs(constraint):
            if ref not in by_id:
                return (f"constraint {constraint.get('type')!r} references unknown "
                        f"entity {ref!r}")
    return None


def _constraint_refs(constraint: dict) -> list[str]:
    """Entity ids a constraint references."""
    if "of" in constraint:
        return [constraint["of"]]
    if "points" in constraint:
        return list(constraint["points"])
    return []


def _add_constraint(system: Any, constraint: dict, workplane: Any,
                    points: dict[str, Any], lines: dict[str, Any]) -> None:
    """Add one supported constraint to the SolveSpace system (bucket 1.1 set)."""
    kind = constraint["type"]
    if kind == "horizontal":
        system.addLineHorizontal(lines[constraint["of"]], wrkpln=workplane,
                                 group=_SKETCH_GROUP)
    elif kind == "vertical":
        system.addLineVertical(lines[constraint["of"]], wrkpln=workplane,
                               group=_SKETCH_GROUP)
    elif kind == "coincident":
        a, b = constraint["points"]
        system.addPointsCoincident(points[a], points[b], wrkpln=workplane,
                                   group=_SKETCH_GROUP)
    elif kind == "distance":
        a, b = constraint["points"]
        system.addPointsDistance(float(constraint["value"]), points[a], points[b],
                                 wrkpln=workplane, group=_SKETCH_GROUP)
    else:
        logger.debug("ignoring unsupported constraint %r in bucket 1.1", kind)


def _result_from(code: int, dof: int, failed: list, positions: dict,
                 feature_id: str) -> SolveResult:
    """Map a py-slvs solve outcome to a SolveResult."""
    if code != 0 or failed:
        message = (f"sketch is over-constrained or inconsistent "
                   f"(solver code {code}, {len(failed)} failing constraint(s))")
        return SolveResult(positions=positions, dof=dof, status="inconsistent",
                           issues=[BuildIssue(node_id=feature_id, message=message)])
    if dof > 0:
        return SolveResult(
            positions=positions, dof=dof, status="under_constrained",
            issues=[BuildIssue(node_id=feature_id,
                               message=f"sketch under-constrained: {dof} free DoF",
                               level="warning")])
    return SolveResult(positions=positions, dof=0, status="well_constrained", issues=[])
