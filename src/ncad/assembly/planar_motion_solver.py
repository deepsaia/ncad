"""Solve a planar mechanism over a driver sweep in a py-slvs 2D workplane, per design section 8.

A planar mechanism (all revolute axes parallel to one plane normal) is a rigid-body motion IN that
plane, which py-slvs solves robustly in a 2D WORKPLANE, unlike the 3D rigid-body MateSolver whose
stacked lower-pair constraints drop the loop-closure of a closed planar loop (verified). Each body's
connectors become workplane points welded rigid by pinned pairwise distances (fixed group when
grounded); each joint becomes a 2D constraint (revolute -> coincident points; slider -> the moving
body's two director points on the ground slideway line, which positions AND anti-spins). The driver
pins the moving connector point at pivot + r*(cos theta, sin theta) in the plane. Each solved body's
in-plane rigid delta (rotation + translation from its rest pose) lifts to a row-major 4x4 via
MechanismPlane, so the trajectory composes with the static rest placements. One class;
module-private helpers. Kinematic only (dynamics -> Phase 14).
"""

import logging
import math
from typing import Any

from py_slvs import slvs

from ncad.assembly.mechanism_plane import MechanismPlane

logger = logging.getLogger(__name__)

_FIX_GROUP = 1
_SOLVE_GROUP = 2
_OK_CODES = (0, 5)


class PlanarMotionSolver:
    """Solves a planar mechanism per driver value in a 2D workplane; returns per-frame 3D deltas."""

    def solve(self, frames: dict, joints: list[dict], ground_ids: set, plane: MechanismPlane,
              driver: dict, values: list[float]) -> list[dict]:
        """One pose dict (instance -> row-major 4x4 delta) per driver value; seeded per step."""
        rest2d = self._project_rest(frames, plane)
        seed2d = {bid: dict(conns) for bid, conns in rest2d.items()}
        pivot2d = rest2d[driver["pivot"]["instance"]][driver["pivot"]["connector"]]
        moving_ref = driver["moving"]
        moving_rest = rest2d[moving_ref["instance"]][moving_ref["connector"]]
        radius = math.hypot(moving_rest[0] - pivot2d[0], moving_rest[1] - pivot2d[1])
        out: list[dict] = []
        for value in values:
            solved2d, status = self._solve_step(
                rest2d, seed2d, joints, ground_ids, driver, pivot2d, radius, value)
            if status in _OK_CODES:
                seed2d = solved2d
            out.append(self._lift(rest2d, solved2d, plane, ground_ids))
        return out

    def _project_rest(self, frames: dict, plane: MechanismPlane) -> dict:
        """Each connector's rest world origin projected to plane 2D coords."""
        rest: dict[str, dict] = {}
        for bid, conns in frames.items():
            rest[bid] = {cid: plane.to_2d(frame.origin) for cid, frame in conns.items()}
        return rest

    def _solve_step(self, rest2d: dict, seed2d: dict, joints: list[dict], ground_ids: set,
                    driver: dict, pivot2d: tuple, radius: float, value: float) -> tuple[dict, int]:
        """Build + solve the workplane for one driver value; return (solved 2D coords, code)."""
        system = slvs.System()
        origin = system.addPoint3dV(0.0, 0.0, 0.0, group=_FIX_GROUP)
        normal = system.addNormal3dV(1.0, 0.0, 0.0, 0.0, group=_FIX_GROUP)
        workplane = system.addWorkplane(origin, normal, group=_FIX_GROUP)
        points: dict[str, dict[str, Any]] = {}
        lines: dict[str, tuple] = {}
        for bid, conns in rest2d.items():
            grounded = bid in ground_ids
            group = _FIX_GROUP if grounded else _SOLVE_GROUP
            handles = {}
            for cid in conns:
                su, sv = seed2d[bid][cid]
                handles[cid] = system.addPoint2dV(workplane, su, sv, group=group)
            points[bid] = handles
            if not grounded:
                self._weld(system, workplane, conns, handles)
            pair = _director_pair(conns)
            if pair is not None:
                lines[bid] = (system.addLineSegment(handles[pair[0]], handles[pair[1]],
                                                    group=group), pair)
        self._apply_joints(system, workplane, joints, points, lines, rest2d)
        self._apply_driver(system, workplane, points, driver, pivot2d, radius, value)
        code = system.solve(group=_SOLVE_GROUP)
        solved = {bid: {cid: _read_point(system, h) for cid, h in handles.items()}
                  for bid, handles in points.items()}
        if code not in _OK_CODES:
            logger.warning("planar motion step (driver=%.3f) solve code %d", value, code)
        return solved, code

    def _weld(self, system: Any, workplane: Any, conns: dict, handles: dict) -> None:
        """Pin every pairwise connector distance so the body is a rigid 2D frame."""
        items = list(conns.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (na, pa), (nb, pb) = items[i], items[j]
                d = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                if d > 1e-9:
                    system.addPointsDistance(d, handles[na], handles[nb], wrkpln=workplane,
                                             group=_SOLVE_GROUP)

    def _apply_joints(self, system: Any, workplane: Any, joints: list[dict], points: dict,
                      lines: dict, rest2d: dict) -> None:
        """Each joint -> its 2D constraint(s): revolute coincident; slider two-point-on-line."""
        busy = _busy_connectors(joints)
        for joint in joints:
            jtype = joint["type"]
            a, b = joint["a"], joint["b"]
            if jtype == "revolute":
                system.addPointsCoincident(points[a["instance"]][a["connector"]],
                                           points[b["instance"]][b["connector"]],
                                           wrkpln=workplane, group=_SOLVE_GROUP)
            elif jtype in ("slider", "point_on_line", "slot"):
                gline = lines.get(a["instance"])
                if gline is None:
                    logger.warning("slider joint %r: ground body has no slideway line", joint["id"])
                    continue
                # Put the referenced connector AND a second, distinct slide connector on the ground
                # slideway line: two points on one line position the body AND kill its rotation (no
                # spin). More robust than point-on-line + parallel under py-slvs's redundancy
                # handling (verified: parallel over-constrains at some driver angles). Both points
                # must be connectors NOT already pinned by another joint (a wrist revolute point
                # would double-pin), so _slider_points picks the farthest-apart FREE pair.
                movers = _slider_points(rest2d[b["instance"]], b["connector"],
                                        busy.get(b["instance"], set()))
                for cid in movers:
                    system.addPointOnLine(points[b["instance"]][cid], gline[0],
                                          wrkpln=workplane, group=_SOLVE_GROUP)
            else:
                logger.debug("planar solver: joint type %r not handled", jtype)

    def _apply_driver(self, system: Any, workplane: Any, points: dict, driver: dict,
                      pivot2d: tuple, radius: float, value: float) -> None:
        """Pin the moving connector point at pivot + radius*(cos theta, sin theta) in the plane."""
        theta = math.radians(value)
        tx = pivot2d[0] + radius * math.cos(theta)
        ty = pivot2d[1] + radius * math.sin(theta)
        target = system.addPoint2dV(workplane, tx, ty, group=_FIX_GROUP)
        moving = driver["moving"]
        system.addPointsCoincident(points[moving["instance"]][moving["connector"]], target,
                                   wrkpln=workplane, group=_SOLVE_GROUP)

    def _lift(self, rest2d: dict, solved2d: dict, plane: MechanismPlane, ground_ids: set) -> dict:
        """Each body's rest->solved 2D rigid delta as a row-major 4x4 (identity when grounded)."""
        poses: dict[str, list[list[float]]] = {}
        for bid, conns in rest2d.items():
            if bid in ground_ids:
                poses[bid] = _identity()
                continue
            pair = _director_pair(conns)
            if pair is None:
                cid = next(iter(conns))
                dx = solved2d[bid][cid][0] - conns[cid][0]
                dy = solved2d[bid][cid][1] - conns[cid][1]
                poses[bid] = plane.delta_matrix(0.0, dx, dy)
                continue
            ca, cb = pair
            ra, rb = conns[ca], conns[cb]
            sa, sb = solved2d[bid][ca], solved2d[bid][cb]
            dtheta = (math.atan2(sb[1] - sa[1], sb[0] - sa[0])
                      - math.atan2(rb[1] - ra[1], rb[0] - ra[0]))
            c, s = math.cos(dtheta), math.sin(dtheta)
            tdx = sa[0] - (c * ra[0] - s * ra[1])
            tdy = sa[1] - (s * ra[0] + c * ra[1])
            poses[bid] = plane.delta_matrix(dtheta, tdx, tdy)
        return poses


def _busy_connectors(joints: list[dict]) -> dict:
    """instance -> connectors pinned by a revolute (so the slider avoids double-pinning them)."""
    busy: dict[str, set] = {}
    for joint in joints:
        if joint["type"] == "revolute":
            for side in ("a", "b"):
                ref = joint[side]
                busy.setdefault(ref["instance"], set()).add(ref["connector"])
    return busy


def _slider_points(conns: dict, anchor: str, busy: set) -> list[str]:
    """The two slideway points: two connectors NOT pinned by another joint, farthest apart.

    Two points on one line position the body AND kill its spin; both must be FREE connectors (a
    connector already pinned by a revolute would be double-pinned, over-constraining). Prefers the
    farthest-apart free pair (longest anti-spin lever). Falls back to the anchor alone if fewer than
    two free connectors exist.
    """
    free = [cid for cid in conns if cid not in busy]
    if len(free) < 2:
        return [anchor] if anchor in conns else free[:1]
    best, best_d = (free[0], free[1]), -1.0
    for i in range(len(free)):
        for j in range(i + 1, len(free)):
            (ux, uy), (vx, vy) = conns[free[i]], conns[free[j]]
            d = math.hypot(ux - vx, uy - vy)
            if d > best_d:
                best, best_d = (free[i], free[j]), d
    return list(best) if best_d > 1e-9 else [anchor]


def _director_pair(conns: dict) -> tuple | None:
    """Two connectors with distinct 2D positions (fix the body angle); None if all coincide."""
    items = list(conns.items())
    if not items:
        return None
    base = items[0]
    for other in items[1:]:
        if math.hypot(base[1][0] - other[1][0], base[1][1] - other[1][1]) > 1e-9:
            return (base[0], other[0])
    return None


def _read_point(system: Any, handle: Any) -> tuple:
    """Solved (u, v) of a workplane point from its entity params."""
    return (system.getParam(system.getEntityParam(handle, 0)).val,
            system.getParam(system.getEntityParam(handle, 1)).val)


def _identity() -> list[list[float]]:
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
