"""Build the DRIVER PIN primitives that impose a driver value on a joint, for the motion solver.

A revolute is driven by a ``drive_to_point`` pin: a WITNESS POINT on the moving connector (its
local origin + radius along local +X) is pinned coincident with a TARGET POINT on the reference
connector (its local origin + radius at the driver angle in the reference x-y plane). A static angle
pin does not solve in py-slvs, but this witness-to-target coincidence does (verified). Both points
are LOCAL to their bodies; the solver transforms each by its body pose before pinning, so the drive
is relative to the reference link and correct regardless of either body's rest placement. A slider /
point_on_line reuses the translational point_plane_distance value pin. Pure vector math over
ConnectorFrames; the moving side (the joint's b_ref) is the driven body.
"""

import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.motion_driver import MotionParamError

_DEFAULT_LEVER = 1.0


def driver_pins(joint_type: str, value: float, a_ref: dict, b_ref: dict,
                frame_a: ConnectorFrame, frame_b: ConnectorFrame) -> list[dict]:
    """The driver primitives imposing ``value`` on ``joint_type`` (b_ref is the moving body)."""
    if joint_type == "revolute":
        return [_revolute_drive(value, a_ref, b_ref, frame_a, frame_b)]
    if joint_type in ("slider", "point_on_line"):
        return [{"kind": "point_plane_distance", "a": "A.origin", "b": "B.plane",
                 "value": float(value), "a_ref": b_ref, "b_ref": a_ref}]
    raise MotionParamError(f"joint type {joint_type!r} has no drivable free axis")


def _revolute_drive(angle_deg: float, a_ref: dict, b_ref: dict,
                    frame_a: ConnectorFrame, frame_b: ConnectorFrame) -> dict:
    """Pin the moving witness (local) to the reference target (local) at ``angle_deg`` about Z."""
    lever = frame_b.radius if frame_b.radius else _DEFAULT_LEVER
    witness = _add(frame_b.origin, _scale(frame_b.x, lever))
    theta = math.radians(angle_deg)
    offset = _add(_scale(frame_a.x, lever * math.cos(theta)),
                  _scale(frame_a.y, lever * math.sin(theta)))
    target = _add(frame_a.origin, offset)
    return {"kind": "drive_to_point", "a_ref": b_ref, "b_ref": a_ref,
            "witness": witness, "target": target}


def _add(p: tuple, q: tuple) -> tuple:
    return (p[0] + q[0], p[1] + q[1], p[2] + q[2])


def _scale(v: tuple, k: float) -> tuple:
    return (v[0] * k, v[1] * k, v[2] * k)
