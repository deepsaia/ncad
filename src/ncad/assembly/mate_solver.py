"""Solve an assembly constraint network with py-slvs, returning solved per-instance placements.

Each movable instance is a py-slvs rigid-body TRANSFORM (translate + unit quaternion, 7 unknown
params) applied to its connector-frame points; ground instances are pinned to their seed pose. Each
normal-form primitive (from MateLowering) becomes one concrete py-slvs constraint. After solving,
each body's pose is read back FROM ITS TRANSFORM PARAM HANDLES (not the transformed entities, which
report stale coords) and converted to a row-major 4x4 by BodyPose. GPL, per the settled solver
decision (design section 8). Verified 3D mechanics: transform POINTS only (rebuild lines in the
solved group); read pose from the param handles; solve codes 0 and 5 are okay.
"""

import logging
from typing import Any

from py_slvs import slvs

from ncad.assembly.body_pose import BodyPose
from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.solve_outcome import SolveOutcome

logger = logging.getLogger(__name__)

_FIX_GROUP = 1
_SOLVE_GROUP = 2
_REDUNDANT_OKAY = 5


class _Body:
    """py-slvs handles for one instance's connectors after transform."""

    def __init__(self, params: tuple | None, connectors: dict) -> None:
        self.params = params  # (dx,dy,dz,qw,qx,qy,qz) param handles, or None for a ground body
        self.connectors = connectors  # connector_id -> {"origin","axis_tip","axis_line"} handles


class MateSolver:
    """Solves an assembly mate network via py-slvs; returns solved placements + status."""

    def solve(self, bodies: dict, primitives: list[dict], ground_ids: set,
              seeds: dict) -> SolveOutcome:
        """Solve ``primitives`` over ``bodies``; return solved placements (mm) + status."""
        # A lock primitive grounds its body (pins it to the seed), so fold locks into ground_ids.
        locked = {p["a_ref"]["instance"] for p in primitives
                  if p["kind"] == "lock" and p.get("a_ref")}
        grounded_all = set(ground_ids) | locked
        system = slvs.System()
        body_handles: dict[str, _Body] = {}
        for instance_id, connectors in bodies.items():
            grounded = instance_id in grounded_all
            body_handles[instance_id] = self._add_body(
                system, connectors, seeds.get(instance_id), grounded)
        handle_to_id: dict[int, str] = {}
        for primitive in primitives:
            before = int(system.ConstraintHandle)
            self._apply(system, primitive, body_handles)
            after = int(system.ConstraintHandle)
            for handle in range(before + 1, after + 1):
                handle_to_id[handle] = primitive.get("id", "?")
        code = system.solve(group=_SOLVE_GROUP, reportFailed=True)
        dof = int(system.Dof)
        reported = _failing_ids(list(system.Failed), handle_to_id)
        placements = {iid: self._read_pose(system, body, seeds.get(iid))
                      for iid, body in body_handles.items()}
        # py-slvs code 5 is redundant-but-consistent: the reported handles are REDUNDANT
        # (removable), not failing. Any other nonzero code / reported handle is a real conflict.
        redundant = reported if code == _REDUNDANT_OKAY else []
        failing = [] if code == _REDUNDANT_OKAY else reported
        status = _status(code, dof, failing)
        return SolveOutcome(placements=placements, dof=dof, status=status, failing_ids=failing,
                            solve_code=code, redundant_ids=redundant)

    def _add_body(self, system: Any, connectors: dict, seed: list | None,
                  grounded: bool) -> _Body:
        """Register one body: its connector geometry, transformed by 7 pose params (or pinned)."""
        # A ground body's params live in the fixed group (constants); a movable body's params live
        # in the solve group as unknowns. Only the translation seeds the initial guess; the rotation
        # seed is identity (the solver refines orientation from the constraints).
        tx, ty, tz, quat = _seed_pose(seed)
        group = _FIX_GROUP if grounded else _SOLVE_GROUP
        dx = system.addParamV(tx, group=group)
        dy = system.addParamV(ty, group=group)
        dz = system.addParamV(tz, group=group)
        qw = system.addParamV(quat[0], group=group)
        qx = system.addParamV(quat[1], group=group)
        qy = system.addParamV(quat[2], group=group)
        qz = system.addParamV(quat[3], group=group)
        pose = (dx, dy, dz, qw, qx, qy, qz)
        params = None if grounded else pose
        handles: dict[str, dict] = {}
        for connector_id, frame in connectors.items():
            handles[connector_id] = self._add_connector(system, frame, pose)
        return _Body(params, handles)

    def _add_connector(self, system: Any, frame: ConnectorFrame, pose: tuple) -> dict:
        """Local connector geometry (origin + Z axis line + X secondary line) into the solved group.

        The Z line carries the primary axis (concentric/parallel/angle); the X (secondary) line lets
        anti-spin joints (fixed/slider/revolute-value) block rotation ABOUT Z via addParallel on X.
        Transform POINTS only (never a LineSegment); rebuild both lines in the solved group.
        """
        dx, dy, dz, qw, qx, qy, qz = pose
        o0 = system.addPoint3dV(frame.origin[0], frame.origin[1], frame.origin[2],
                                group=_FIX_GROUP)
        ztip = (frame.origin[0] + frame.z[0], frame.origin[1] + frame.z[1],
                frame.origin[2] + frame.z[2])
        z0 = system.addPoint3dV(ztip[0], ztip[1], ztip[2], group=_FIX_GROUP)
        xtip = (frame.origin[0] + frame.x[0], frame.origin[1] + frame.x[1],
                frame.origin[2] + frame.x[2])
        x0 = system.addPoint3dV(xtip[0], xtip[1], xtip[2], group=_FIX_GROUP)
        origin = system.addTransform(o0, dx, dy, dz, qw, qx, qy, qz, group=_SOLVE_GROUP)
        axis_tip = system.addTransform(z0, dx, dy, dz, qw, qx, qy, qz, group=_SOLVE_GROUP)
        sec_tip = system.addTransform(x0, dx, dy, dz, qw, qx, qy, qz, group=_SOLVE_GROUP)
        axis_line = system.addLineSegment(origin, axis_tip, group=_SOLVE_GROUP)
        secondary_line = system.addLineSegment(origin, sec_tip, group=_SOLVE_GROUP)
        return {"origin": origin, "axis_tip": axis_tip, "axis_line": axis_line,
                "secondary_line": secondary_line}

    def _apply(self, system: Any, primitive: dict, bodies: dict) -> None:
        """Emit one py-slvs constraint for a primitive. Unknown kinds are logged and skipped."""
        kind = primitive["kind"]
        a_o, a_axis, a_sec = self._side(primitive, "a_ref", bodies)
        b_o, b_axis, b_sec = self._side(primitive, "b_ref", bodies)
        if kind == "points_coincident":
            system.addPointsCoincident(a_o, b_o, group=_SOLVE_GROUP)
        elif kind in ("parallel_dirs", "anti_parallel_dirs"):
            # Axis-line parallelism. Sense (opposed vs same) is carried by the coincident origin +
            # the seed orientation; addParallel aligns the lines' directions.
            system.addParallel(a_axis, b_axis, group=_SOLVE_GROUP)
        elif kind == "secondary_parallel":
            # Anti-spin: align the connectors' secondary (X) axes so rotation about the shared Z is
            # blocked. Same addParallel math as parallel_dirs, on the X lines instead of Z.
            system.addParallel(a_sec, b_sec, group=_SOLVE_GROUP)
        elif kind == "axes_coincident":
            # Line-line coincidence: A's origin lies on B's axis AND the axes are parallel.
            system.addPointOnLine(a_o, b_axis, group=_SOLVE_GROUP)
            system.addParallel(a_axis, b_axis, group=_SOLVE_GROUP)
        elif kind == "point_on_line":
            # A.origin constrained to B's axis line (the slot's line); leaves translation along it.
            system.addPointOnLine(a_o, b_axis, group=_SOLVE_GROUP)
        elif kind == "point_in_plane":
            # A.origin lies in B's plane: its projection onto B's axis is at distance 0 from
            # B.origin. addPointsProjectDistance(d, p1, p2, direction_line) is that projection.
            system.addPointsProjectDistance(0.0, a_o, b_o, b_axis, group=_SOLVE_GROUP)
        elif kind == "point_plane_distance":
            # Signed gap along B's normal: A.origin projects onto B's axis at distance `value`
            # from B.origin.
            system.addPointsProjectDistance(float(primitive["value"]), a_o, b_o, b_axis,
                                            group=_SOLVE_GROUP)
        elif kind == "points_distance":
            system.addPointsDistance(float(primitive["value"]), a_o, b_o, group=_SOLVE_GROUP)
        elif kind == "dirs_angle":
            system.addAngle(float(primitive["value"]), False, a_axis, b_axis, group=_SOLVE_GROUP)
        elif kind == "lock":
            # A locked body is grounded at solve setup (folded into ground_ids); nothing to add.
            pass
        else:
            logger.debug("mate solver: primitive kind %r not handled in this task", kind)

    def _side(self, primitive: dict, ref_key: str, bodies: dict) -> tuple:
        """Return (origin, axis_line, secondary_line) for the a/b side, or (None, None, None)."""
        ref = primitive.get(ref_key)
        if ref is None:
            return None, None, None
        connector = bodies[ref["instance"]].connectors[ref["connector"]]
        return connector["origin"], connector["axis_line"], connector["secondary_line"]

    def _read_pose(self, system: Any, body: _Body, seed: list | None) -> list[list[float]]:
        """Read a body's solved pose from its transform param handles -> row-major 4x4."""
        if body.params is None:
            # Ground body: it never moved; return its seed pose unchanged.
            return [row[:] for row in (seed or _identity())]
        dx, dy, dz, qw, qx, qy, qz = body.params
        translate = (system.getParam(dx).val, system.getParam(dy).val, system.getParam(dz).val)
        quaternion = (system.getParam(qw).val, system.getParam(qx).val,
                      system.getParam(qy).val, system.getParam(qz).val)
        return BodyPose().matrix(translate, quaternion)


def _seed_pose(seed: list | None) -> tuple:
    """Extract (tx, ty, tz, (qw,qx,qy,qz)) from a seed 4x4; identity rotation always.

    Only the translation seeds the solver's initial guess; the rotation seed is identity (the
    solver refines orientation from the constraints). A better rotation seed is a 5.3+ refinement.
    """
    if not seed:
        return 0.0, 0.0, 0.0, (1.0, 0.0, 0.0, 0.0)
    return float(seed[3][0]), float(seed[3][1]), float(seed[3][2]), (1.0, 0.0, 0.0, 0.0)


def _identity() -> list[list[float]]:
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _status(code: int, dof: int, failing: list) -> str:
    """Map a py-slvs solve code + dof to a status string."""
    if code not in (0, _REDUNDANT_OKAY) or failing:
        return "over_constrained"
    if dof > 0:
        return "under_constrained"
    return "solved"


def _failing_ids(failed: list, handle_to_id: dict) -> list[str]:
    """Authored mate ids for the solver's failing handles, in declaration order (deduped)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for handle in failed:
        label = handle_to_id.get(int(handle))
        if label is not None and label not in seen:
            seen.add(label)
            ordered.append(label)
    return ordered
