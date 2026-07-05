"""py-slvs (SolveSpace) implementation of the SketchSolver seam (design section 5).

Maps our 2D entities/constraints onto a SolveSpace System with a fixed base workplane
(group 1) and the sketch entities in the solved group (group 2), runs the solver, and
reads back solved point coordinates. GPL, per the settled solver-licensing decision
(design section 8). Entities/constraints reference each other by our string ids; a
dangling reference is reported as an id-tagged error before the solver runs.
"""

import logging
import math
from typing import Any

from py_slvs import slvs

from ncad.ops.build_issue import BuildIssue
from ncad.sketch.sketch_solver import SketchSolver
from ncad.sketch.solve_result import SolveResult

logger = logging.getLogger(__name__)

_BASE_GROUP = 1
_SKETCH_GROUP = 2


class ConstraintError(Exception):
    """A constraint cannot be applied (type mismatch or missing data); reported by id."""


class _Ctx:
    """The handles and entity dicts a constraint handler needs to resolve ids."""

    def __init__(self, workplane: Any, points: dict, curves: dict, entities: dict) -> None:
        self.workplane = workplane
        self.points = points
        self.curves = curves
        self.entities = entities


class SlvsSolver(SketchSolver):
    """Solves sketches with SolveSpace via py-slvs."""

    # Constraint type -> handler method name. Handlers add the constraint to the system;
    # driven dimensions are skipped here and measured after solving.
    _CONSTRAINT_HANDLERS = {
        "horizontal": "_c_horizontal", "vertical": "_c_vertical",
        "coincident": "_c_coincident", "distance": "_c_distance", "radius": "_c_radius",
        "parallel": "_c_parallel", "perpendicular": "_c_perpendicular",
        "equal": "_c_equal", "symmetric": "_c_symmetric", "midpoint": "_c_midpoint",
        "point_on": "_c_point_on", "collinear": "_c_collinear",
        "concentric": "_c_concentric", "tangent": "_c_tangent", "fix": "_c_fix",
        "angle": "_c_angle", "diameter": "_c_diameter",
    }

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
        curve_handles: dict[str, Any] = {}
        circle_dist: dict[str, Any] = {}
        for entity in entities:
            if entity["type"] == "point":
                u, v = entity["at"]
                point_handles[entity["id"]] = system.addPoint2dV(
                    workplane, float(u), float(v), group=_SKETCH_GROUP)
        for entity in entities:
            kind = entity["type"]
            if kind == "line":
                curve_handles[entity["id"]] = system.addLineSegment(
                    point_handles[entity["p1"]], point_handles[entity["p2"]],
                    group=_SKETCH_GROUP)
            elif kind == "circle":
                dist = system.addDistanceV(float(entity.get("radius", 1.0)),
                                           group=_SKETCH_GROUP)
                circle_dist[entity["id"]] = dist
                normal2d = system.addNormal2d(workplane, group=_SKETCH_GROUP)
                curve_handles[entity["id"]] = system.addCircleV(
                    point_handles[entity["center"]], normal2d, dist, group=_SKETCH_GROUP)
            elif kind == "arc":
                curve_handles[entity["id"]] = system.addArcOfCircle(
                    workplane, point_handles[entity["center"]],
                    point_handles[entity["start"]], point_handles[entity["end"]],
                    group=_SKETCH_GROUP)

        for entity in entities:
            if entity.get("construction"):
                for pid in _defining_points(entity):
                    system.addWhereDragged(point_handles[pid], wrkpln=workplane,
                                           group=_SKETCH_GROUP)

        ctx = _Ctx(workplane, point_handles, curve_handles, by_id)
        try:
            for constraint in constraints:
                self._apply(system, constraint, ctx)
        except ConstraintError as exc:
            return SolveResult(positions={}, dof=0, status="inconsistent",
                               issues=[BuildIssue(node_id=feature_id, message=str(exc))])

        code = system.solve(group=_SKETCH_GROUP, reportFailed=True)
        dof = int(system.Dof)
        failed = list(system.Failed)
        positions = {
            pid: (system.getParam(system.getEntityParam(handle, 0)).val,
                  system.getParam(system.getEntityParam(handle, 1)).val)
            for pid, handle in point_handles.items()
        }
        radii = {
            cid: system.getParam(system.getEntityParam(system.getEntity(handle).distance, 0)).val
            for cid, handle in curve_handles.items() if cid in circle_dist
        }
        measurements: dict[str, float] = {}
        for constraint in constraints:
            if constraint.get("driven"):
                measurements[constraint["id"]] = _measure(constraint, positions, radii, by_id)
        return _result_from(code, dof, failed, positions, feature_id, radii, measurements)

    def _apply(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        """Dispatch one constraint to its handler; skip driven dims (measured post-solve)."""
        kind = constraint.get("type", "")
        if constraint.get("driven"):
            if not constraint.get("id"):
                raise ConstraintError(f"driven {kind} dimension needs an 'id'")
            return
        handler = self._CONSTRAINT_HANDLERS.get(kind)
        if handler is None:
            logger.debug("ignoring unsupported constraint %r", kind)
            return
        getattr(self, handler)(system, constraint, ctx)

    def _c_horizontal(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        system.addLineHorizontal(ctx.curves[constraint["of"]], wrkpln=ctx.workplane,
                                 group=_SKETCH_GROUP)

    def _c_vertical(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        system.addLineVertical(ctx.curves[constraint["of"]], wrkpln=ctx.workplane,
                               group=_SKETCH_GROUP)

    def _c_coincident(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["points"]
        system.addPointsCoincident(ctx.points[a], ctx.points[b], wrkpln=ctx.workplane,
                                   group=_SKETCH_GROUP)

    def _c_distance(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["points"]
        system.addPointsDistance(float(constraint["value"]), ctx.points[a], ctx.points[b],
                                 wrkpln=ctx.workplane, group=_SKETCH_GROUP)

    def _c_radius(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        system.addDiameter(2.0 * float(constraint["value"]), ctx.curves[constraint["of"]],
                           group=_SKETCH_GROUP)

    def _c_parallel(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["lines"]
        system.addParallel(ctx.curves[a], ctx.curves[b], wrkpln=ctx.workplane,
                           group=_SKETCH_GROUP)

    def _c_perpendicular(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["lines"]
        system.addPerpendicular(ctx.curves[a], ctx.curves[b], wrkpln=ctx.workplane,
                                group=_SKETCH_GROUP)

    def _c_equal(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["of"]
        ta, tb = ctx.entities[a]["type"], ctx.entities[b]["type"]
        if ta == "line" and tb == "line":
            system.addEqualLength(ctx.curves[a], ctx.curves[b], wrkpln=ctx.workplane,
                                  group=_SKETCH_GROUP)
        elif ta in ("circle", "arc") and tb in ("circle", "arc"):
            system.addEqualRadius(ctx.curves[a], ctx.curves[b], group=_SKETCH_GROUP)
        else:
            raise ConstraintError(f"equal needs two lines or two curves, got {ta}+{tb}")

    def _c_symmetric(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["points"]
        system.addSymmetricLine(ctx.points[a], ctx.points[b],
                                ctx.curves[constraint["about"]], ctx.workplane,
                                group=_SKETCH_GROUP)

    def _c_midpoint(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        system.addMidPoint(ctx.points[constraint["point"]], ctx.curves[constraint["of"]],
                           wrkpln=ctx.workplane, group=_SKETCH_GROUP)

    def _c_point_on(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        point = ctx.points[constraint["point"]]
        target = constraint["of"]
        if ctx.entities[target]["type"] == "line":
            system.addPointOnLine(point, ctx.curves[target], wrkpln=ctx.workplane,
                                  group=_SKETCH_GROUP)
        else:
            system.addPointOnCircle(point, ctx.curves[target], group=_SKETCH_GROUP)

    def _c_collinear(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["lines"]
        system.addParallel(ctx.curves[a], ctx.curves[b], wrkpln=ctx.workplane,
                           group=_SKETCH_GROUP)
        endpoint = ctx.points[ctx.entities[b]["p1"]]
        system.addPointOnLine(endpoint, ctx.curves[a], wrkpln=ctx.workplane,
                              group=_SKETCH_GROUP)

    def _c_concentric(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["of"]
        center_a = ctx.points[ctx.entities[a]["center"]]
        center_b = ctx.points[ctx.entities[b]["center"]]
        system.addPointsCoincident(center_a, center_b, wrkpln=ctx.workplane,
                                   group=_SKETCH_GROUP)

    def _c_tangent(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["of"]
        ta, tb = ctx.entities[a]["type"], ctx.entities[b]["type"]
        if ta == "arc" and tb == "line":
            arc_id, line_id = a, b
        elif tb == "arc" and ta == "line":
            arc_id, line_id = b, a
        else:
            arc_id = line_id = None
        if arc_id is not None:
            at_end = _touches_arc_end(ctx.entities[arc_id], ctx.entities[line_id])
            system.addArcLineTangent(at_end, ctx.curves[arc_id], ctx.curves[line_id],
                                     group=_SKETCH_GROUP)
        elif ta in ("arc", "circle") and tb in ("arc", "circle"):
            system.addCurvesTangent(True, False, ctx.curves[a], ctx.curves[b],
                                    wrkpln=ctx.workplane, group=_SKETCH_GROUP)
        else:
            raise ConstraintError(f"tangent needs arc+line or two curves, got {ta}+{tb}")

    def _c_fix(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        target = constraint["of"]
        etype = ctx.entities[target]["type"]
        if etype == "point":
            system.addWhereDragged(ctx.points[target], wrkpln=ctx.workplane,
                                   group=_SKETCH_GROUP)
        elif etype == "line":
            for key in ("p1", "p2"):
                system.addWhereDragged(ctx.points[ctx.entities[target][key]],
                                       wrkpln=ctx.workplane, group=_SKETCH_GROUP)
        else:
            system.addWhereDragged(ctx.points[ctx.entities[target]["center"]],
                                   wrkpln=ctx.workplane, group=_SKETCH_GROUP)

    def _c_angle(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        a, b = constraint["lines"]
        system.addAngle(float(constraint["value"]), False, ctx.curves[a], ctx.curves[b],
                        wrkpln=ctx.workplane, group=_SKETCH_GROUP)

    def _c_diameter(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        system.addDiameter(float(constraint["value"]), ctx.curves[constraint["of"]],
                           group=_SKETCH_GROUP)


def _missing_reference(entities: list[dict], constraints: list[dict],
                       by_id: dict[str, dict]) -> str | None:
    """The first dangling entity reference, as an error message, or None."""
    ref_keys = {"line": ("p1", "p2"), "circle": ("center",),
                "arc": ("center", "start", "end")}
    for entity in entities:
        for key in ref_keys.get(entity.get("type", ""), ()):
            if entity.get(key) not in by_id:
                return (f"{entity.get('type')} {entity.get('id')!r} references unknown "
                        f"point {entity.get(key)!r}")
    for constraint in constraints:
        for ref in _constraint_refs(constraint):
            if ref not in by_id:
                return (f"constraint {constraint.get('type')!r} references unknown "
                        f"entity {ref!r}")
    return None


def _constraint_refs(constraint: dict) -> list[str]:
    """Entity ids a constraint references (across all reference-field shapes)."""
    refs: list[str] = []
    for key in ("lines", "points"):
        value = constraint.get(key)
        if isinstance(value, list):
            refs.extend(value)
    for key in ("about", "point"):
        value = constraint.get(key)
        if isinstance(value, str):
            refs.append(value)
    of = constraint.get("of")
    if isinstance(of, str):
        refs.append(of)
    elif isinstance(of, list):
        refs.extend(of)
    return refs


def _defining_points(entity: dict) -> list[str]:
    """Point ids that define an entity's position (for pinning construction geometry)."""
    kind = entity.get("type")
    if kind == "point":
        return [entity["id"]]
    if kind == "line":
        return [entity["p1"], entity["p2"]]
    if kind == "arc":
        return [entity["center"], entity["start"], entity["end"]]
    if kind == "circle":
        return [entity["center"]]
    return []


def _touches_arc_end(arc: dict, line: dict) -> bool:
    """Whether the line meets the arc at the arc's end point (else its start)."""
    return arc["end"] in (line.get("p1"), line.get("p2"))


def _measure(constraint: dict, positions: dict, radii: dict, entities: dict) -> float:
    """Measure a driven (reference) dimension from the solved geometry."""
    kind = constraint["type"]
    if kind == "distance":
        a, b = constraint["points"]
        (ax, ay), (bx, by) = positions[a], positions[b]
        return math.hypot(bx - ax, by - ay)
    if kind in ("radius", "diameter"):
        radius = radii.get(constraint["of"], 0.0)
        return radius if kind == "radius" else 2.0 * radius
    if kind == "angle":
        a, b = constraint["lines"]
        return _line_angle_degrees(entities[a], entities[b], positions)
    if kind == "arc_length":
        return _arc_length(entities[constraint["of"]], positions)
    raise ConstraintError(f"cannot measure driven dimension of type {kind!r}")


def _line_direction(line: dict, positions: dict) -> tuple[float, float]:
    """Unit-ish direction vector of a line from its solved endpoints."""
    (ax, ay), (bx, by) = positions[line["p1"]], positions[line["p2"]]
    return bx - ax, by - ay


def _line_angle_degrees(line_a: dict, line_b: dict, positions: dict) -> float:
    """Angle between two lines' solved directions, in degrees (0..180)."""
    ax, ay = _line_direction(line_a, positions)
    bx, by = _line_direction(line_b, positions)
    dot = ax * bx + ay * by
    mag = math.hypot(ax, ay) * math.hypot(bx, by)
    if mag < 1e-12:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / mag))))


def _arc_length(arc: dict, positions: dict) -> float:
    """Arc length = radius * swept angle, from the arc's solved center/start/end."""
    cx, cy = positions[arc["center"]]
    sx, sy = positions[arc["start"]]
    ex, ey = positions[arc["end"]]
    radius = math.hypot(sx - cx, sy - cy)
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    sweep = a1 - a0
    while sweep <= 0.0:
        sweep += 2.0 * math.pi
    return radius * sweep


def _result_from(code: int, dof: int, failed: list, positions: dict,
                 feature_id: str, radii: dict, measurements: dict) -> SolveResult:
    """Map a py-slvs solve outcome to a SolveResult."""
    if code != 0 or failed:
        message = (f"sketch is over-constrained or inconsistent "
                   f"(solver code {code}, {len(failed)} failing constraint(s))")
        return SolveResult(positions=positions, dof=dof, status="inconsistent",
                           issues=[BuildIssue(node_id=feature_id, message=message)],
                           radii=radii, measurements=measurements)
    if dof > 0:
        return SolveResult(
            positions=positions, dof=dof, status="under_constrained",
            issues=[BuildIssue(node_id=feature_id,
                               message=f"sketch under-constrained: {dof} free DoF",
                               level="warning")], radii=radii, measurements=measurements)
    return SolveResult(positions=positions, dof=0, status="well_constrained", issues=[],
                       radii=radii, measurements=measurements)
