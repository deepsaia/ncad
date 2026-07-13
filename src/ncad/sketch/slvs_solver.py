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
        "minor_radius": "_c_minor_radius", "smooth": "_c_smooth",
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
            elif kind == "ellipse":
                # A full ellipse has no solver curve entity (py-slvs has no ellipse), but its
                # minor radius is a solved distance so it can be dimensioned/measured like a
                # circle radius; its center + major_axis_end points carry the rest of the DOF.
                circle_dist[entity["id"]] = system.addDistanceV(
                    float(entity["minor_radius"]), group=_SKETCH_GROUP)
            # bezier/interpolated are NOT registered as solver curves: their defining
            # points (registered above) carry all DOF; the curve is derived downstream.
            # ellipse_arc/conic are the same: py-slvs has no such primitive, so their
            # defining points carry the DOF and the analytic curve is derived by the kernel.

        # Construction (reference) and fixed (offset-derived) entities are dimensionally
        # locked: pin each defining point once (a point may back several such entities),
        # and pin a circle's radius via a diameter constraint.
        pinned_points: set = set()
        for entity in entities:
            if not (entity.get("construction") or entity.get("fixed")):
                continue
            for pid in _defining_points(entity):
                if pid not in pinned_points:
                    system.addWhereDragged(point_handles[pid], wrkpln=workplane,
                                           group=_SKETCH_GROUP)
                    pinned_points.add(pid)
            if entity["type"] == "circle":
                system.addDiameter(2.0 * float(entity["radius"]),
                                   curve_handles[entity["id"]], group=_SKETCH_GROUP)

        ctx = _Ctx(workplane, point_handles, curve_handles, by_id)
        handle_to_id: dict[int, str] = {}
        try:
            for index, constraint in enumerate(constraints):
                before = int(system.ConstraintHandle)
                self._apply(system, constraint, ctx)
                after = int(system.ConstraintHandle)
                label = constraint.get("id") or f"{constraint.get('type', '?')}#{index}"
                for handle in range(before + 1, after + 1):
                    handle_to_id[handle] = label
        except ConstraintError as exc:
            return SolveResult(positions={}, dof=0, status="inconsistent",
                               issues=[BuildIssue(node_id=feature_id, message=str(exc))])

        code = system.solve(group=_SKETCH_GROUP, reportFailed=True)
        dof = int(system.Dof)
        failed = list(system.Failed)
        failing_ids = _failing_ids(failed, handle_to_id)
        positions = {
            pid: (system.getParam(system.getEntityParam(handle, 0)).val,
                  system.getParam(system.getEntityParam(handle, 1)).val)
            for pid, handle in point_handles.items()
        }
        radii = {
            cid: system.getParam(system.getEntityParam(system.getEntity(handle).distance, 0)).val
            for cid, handle in curve_handles.items() if cid in circle_dist
        }
        # An ellipse's minor radius lives in circle_dist but has no curve handle (it is not a
        # solver curve); read it straight from its distance param.
        for eid, dist in circle_dist.items():
            if eid not in radii:
                radii[eid] = system.getParam(system.getEntityParam(dist, 0)).val
        measurements: dict[str, float] = {}
        for constraint in constraints:
            if constraint.get("driven"):
                measurements[constraint["id"]] = _measure(constraint, positions, radii, by_id)
        drifted = _fixed_points_held(entities, positions)
        return _result_from(code, dof, failed, positions, feature_id, radii,
                            measurements, drifted, failing_ids)

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

    def _c_smooth(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        """G1 tangent continuity between two curves sharing an endpoint.

        py-slvs expresses G1 (tangent), not G2 (curvature), so a ``continuity: g2`` request is
        refused clearly rather than silently solved as G1. Point-defined curves (spline /
        ellipse / ellipse_arc / conic) have no solver curve entity (their shape is carried by
        their points), so continuity on them is not solver-expressible and is refused too.
        """
        if str(constraint.get("continuity", "g1")).lower() == "g2":
            raise ConstraintError("g2 curvature continuity is not supported by the sketch "
                                  "solver (py-slvs expresses g1 tangent only)")
        a, b = constraint["of"]
        for cid in (a, b):
            if cid not in ctx.curves:
                raise ConstraintError(
                    f"smooth needs two solver curves (line/arc/circle); {cid!r} is a "
                    "point-defined curve (spline/ellipse/conic) with no tangent handle")
        ta, tb = ctx.entities[a]["type"], ctx.entities[b]["type"]
        if ta == "arc" and tb == "line":
            system.addArcLineTangent(_touches_arc_end(ctx.entities[a], ctx.entities[b]),
                                     ctx.curves[a], ctx.curves[b], group=_SKETCH_GROUP)
        elif ta == "line" and tb == "arc":
            system.addArcLineTangent(_touches_arc_end(ctx.entities[b], ctx.entities[a]),
                                     ctx.curves[b], ctx.curves[a], group=_SKETCH_GROUP)
        elif ta in ("arc", "circle") and tb in ("arc", "circle"):
            system.addCurvesTangent(True, False, ctx.curves[a], ctx.curves[b],
                                    wrkpln=ctx.workplane, group=_SKETCH_GROUP)
        else:
            raise ConstraintError(f"smooth (g1) needs arc/line/circle curves, got {ta}+{tb}")

    def _c_minor_radius(self, system: Any, constraint: dict, ctx: _Ctx) -> None:
        # A DRIVEN minor_radius is measured post-solve (handled in _apply, never reaches here).
        # A DRIVING minor_radius would force the ellipse's minor-axis distance to a value, but
        # py-slvs offers no value-equality on a bare distance handle (only diameter/radius on a
        # circle/arc curve entity, and an ellipse has none). The entity's own `minor_radius`
        # seed already sets it, so a driving dimension is refused clearly rather than ignored.
        raise ConstraintError(
            "a driving minor_radius dimension is not supported (author it as driven, or set "
            "minor_radius on the ellipse entity)")


def _missing_reference(entities: list[dict], constraints: list[dict],
                       by_id: dict[str, dict]) -> str | None:
    """The first dangling entity reference, as an error message, or None."""
    ref_keys = {"line": ("p1", "p2"), "circle": ("center",),
                "arc": ("center", "start", "end"),
                "ellipse": ("center", "major_axis_end"),
                "ellipse_arc": ("center", "major_axis_end", "start", "end"),
                "conic": ("start", "apex", "end")}
    # A spline/bezier references its defining points as a LIST under "points", not as
    # scalar fields, so it is checked separately from the scalar ref_keys above.
    list_ref_keys = {"bezier": ("points",), "interpolated": ("points",)}
    for entity in entities:
        etype = entity.get("type", "")
        for key in ref_keys.get(etype, ()):
            if entity.get(key) not in by_id:
                return (f"{etype} {entity.get('id')!r} references unknown "
                        f"point {entity.get(key)!r}")
        for key in list_ref_keys.get(etype, ()):
            for ref in entity.get(key, []):
                if ref not in by_id:
                    return (f"{etype} {entity.get('id')!r} references unknown "
                            f"point {ref!r}")
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
    if kind in ("bezier", "interpolated"):
        return list(entity["points"])
    if kind == "ellipse":
        return [entity["center"], entity["major_axis_end"]]
    if kind == "ellipse_arc":
        return [entity["center"], entity["major_axis_end"], entity["start"], entity["end"]]
    if kind == "conic":
        return [entity["start"], entity["apex"], entity["end"]]
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
    if kind == "minor_radius":
        return radii.get(constraint["of"], 0.0)
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


# SolveSpace result codes: 0 OKAY, 1 INCONSISTENT, 2 DIDNT_CONVERGE, 3 TOO_MANY_UNKNOWNS.
# py-slvs additionally returns 5 for a *redundant-but-consistent* system: every constraint
# is satisfied and the geometry solved, but a constraint is mathematically redundant. This
# is expected for fully-fixed geometry whose points are each pinned while the entity also
# couples them (a fixed arc's equal-radius, an offset curve sharing a pinned center), so we
# accept code 5 as solved. Genuine failures (1/2/3) and any reported failing constraints
# still make the sketch inconsistent.
_REDUNDANT_OKAY = 5


def _fixed_points_held(entities: list[dict], positions: dict) -> str | None:
    """Return the id of a ``fixed`` point that drifted off its seed, or None if all held.

    A consistent solve must leave every fixed point at its declared seed; a drift means
    the solver silently relaxed a pin (masked over-pinning), which we reject. This closes
    the theoretical gap in accepting the redundant-but-consistent solver code.
    """
    for entity in entities:
        if entity.get("type") != "point" or not entity.get("fixed"):
            continue
        solved = positions.get(entity["id"])
        if solved is None:
            continue
        sx, sy = float(entity["at"][0]), float(entity["at"][1])
        if abs(solved[0] - sx) > 1e-6 or abs(solved[1] - sy) > 1e-6:
            return entity["id"]
    return None


def _failing_ids(failed: list, handle_to_id: dict[int, str]) -> list[str]:
    """Authored-constraint ids for the solver's failing handles, in declaration order.

    A failing handle that maps to no authored constraint (a fixed/construction pin) is
    skipped; the visible over-constraint is attributed to the authored constraints.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for handle in failed:
        label = handle_to_id.get(int(handle))
        if label is not None and label not in seen:
            seen.add(label)
            ordered.append(label)
    return ordered


def _result_from(code: int, dof: int, failed: list, positions: dict,
                 feature_id: str, radii: dict, measurements: dict,
                 drifted: str | None = None,
                 failing_ids: list[str] | None = None) -> SolveResult:
    """Map a py-slvs solve outcome to a SolveResult."""
    failing = failing_ids or []
    # Code 5 (redundant-but-consistent) reports its redundant pins in ``failed``, but the
    # geometry solved, so it is accepted. Any other nonzero code is a genuine failure, and
    # a fixed point that drifted off its seed means the redundancy masked a real conflict.
    if code not in (0, _REDUNDANT_OKAY) or drifted is not None:
        detail = (f"fixed point {drifted!r} moved off its seed" if drifted is not None
                  else f"solver code {code}, {len(failed)} failing constraint(s)")
        message = f"sketch is over-constrained or inconsistent ({detail})"
        return SolveResult(positions=positions, dof=dof, status="inconsistent",
                           issues=[BuildIssue(node_id=feature_id, message=message)],
                           radii=radii, measurements=measurements, failing_ids=failing)
    if dof > 0:
        return SolveResult(
            positions=positions, dof=dof, status="under_constrained",
            issues=[BuildIssue(node_id=feature_id,
                               message=f"sketch under-constrained: {dof} free DoF",
                               level="warning")], radii=radii, measurements=measurements,
            failing_ids=failing)
    return SolveResult(positions=positions, dof=0, status="well_constrained", issues=[],
                       radii=radii, measurements=measurements, failing_ids=failing)
