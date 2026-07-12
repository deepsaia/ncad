"""Lower a lower-pair joint to primitive constraint records + its DoF signature (bucket 5.4a).

Mirrors MateLowering: each joint type maps to the existing primitive kinds (plus secondary_parallel
for anti-spin), reusing the closed solver core. A valueless joint contributes only positioning
primitives (leaving its DoF free); an optional static `value` adds the pinning primitive(s). The
signature (free-axis records) is declared by joint type via SIGNATURES. Pure data (no solver,
no kernel).
"""

import logging

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.joint_signature import SIGNATURES, FreeAxis

logger = logging.getLogger(__name__)


class JointError(Exception):
    """A joint cannot be lowered (unknown type or bad value); reported by joint id."""


class JointLowering:
    """Maps a lower-pair joint to primitive records + its DoF signature."""

    def lower(self, joint: dict, frame_a: ConnectorFrame,
              frame_b: ConnectorFrame | None) -> tuple[list[dict], list[FreeAxis]]:
        """Return (primitive records, signature) for ``joint``; raise JointError on a bad type."""
        jtype = joint.get("type", "")
        if jtype not in SIGNATURES:
            raise JointError(f"unknown joint type {jtype!r} (joint {joint.get('id')!r})")
        signature = self._signature(jtype, joint)
        value = joint.get("value")
        prims = self._positioning(jtype)
        prims.extend(self._value_pins(jtype, value, joint))
        return prims, signature

    def _signature(self, jtype: str, joint: dict) -> list[FreeAxis]:
        """The declared signature; screw's is rebuilt with the joint's pitch (else static)."""
        if jtype == "screw":
            pitch = joint.get("pitch")
            return [FreeAxis("screw", "Z", pitch=None if pitch is None else float(pitch))]
        return SIGNATURES[jtype]

    def _positioning(self, jtype: str) -> list[dict]:
        """The primitives that position the two bodies, leaving the joint's DoF free."""
        if jtype == "fixed":
            return [_p("points_coincident", "A.origin", "B.origin"),
                    _p("anti_parallel_dirs", "A.axis", "B.axis"),
                    _p("secondary_parallel", "A.secondary", "B.secondary")]
        if jtype == "revolute":
            return [_p("axes_coincident", "A.axis", "B.axis"),
                    _p("point_in_plane", "A.origin", "B.plane")]
        if jtype == "slider":
            return [_p("axes_coincident", "A.axis", "B.axis"),
                    _p("secondary_parallel", "A.secondary", "B.secondary")]
        if jtype == "cylindrical":
            return [_p("axes_coincident", "A.axis", "B.axis")]
        if jtype == "planar":
            return [_p("point_in_plane", "A.origin", "B.plane"),
                    _p("parallel_dirs", "A.axis", "B.axis")]
        if jtype == "ball":
            return [_p("points_coincident", "A.origin", "B.origin")]
        if jtype == "screw":
            # Coaxial like cylindrical; the rotation+axial coupling is enforced by the value pins
            # (valued) or driven in Phase 6 (valueless). Leaves the cylindrical freedom otherwise.
            return [_p("axes_coincident", "A.axis", "B.axis")]
        # point_on_line / slot
        return [_p("point_on_line", "A.origin", "B.axis")]

    def _value_pins(self, jtype: str, value: float | int | str | list | tuple | None,
                    joint: dict) -> list[dict]:
        """The extra primitives that pin the free DoF when a static value is given.

        5.4a fully supports value-pinning for the 1-DoF joints (revolute/slider/point_on_line);
        cylindrical/planar/ball accept a value but pinning multi-DoF is deferred (best-effort: the
        DoF stays free). A wrong-typed value raises.
        """
        if value is None:
            return []
        if jtype == "slider":
            return [_p("point_plane_distance", "A.origin", "B.plane", _num(value, joint))]
        if jtype == "point_on_line":
            return [_p("point_plane_distance", "A.origin", "B.plane", _num(value, joint))]
        if jtype == "screw":
            # A screw's value is the turn angle; its coupled axial travel (theta/360 * pitch) pins
            # the DEPTH, which solves statically. The ROTATION pin is deferred to Phase 6 (angular
            # pinning does not solve statically here, see below), so a valued screw fixes depth and
            # leaves rotation free.
            theta = _num(value, joint)
            pitch = joint.get("pitch")
            if pitch is None:
                raise JointError(f"screw joint {joint.get('id')!r} with a value needs a pitch")
            return [_p("point_plane_distance", "A.origin", "B.plane", theta / 360.0 * float(pitch))]
        # Rotation-pinning (revolute angle, cylindrical/planar/ball multi-DoF) is DEFERRED to Phase
        # 6 forward kinematics: an angular value does not pin a static solve (addAngle on coaxial
        # frames is inconsistent/redundant), so the joint solves with that DoF free. Only the
        # TRANSLATIONAL pins above (slider/point_on_line/screw-depth) solve statically in 5.4b.
        logger.debug("rotation value-pinning for %r is deferred to Phase 6; leaving that DoF free",
                     jtype)
        return []


def _p(kind: str, a: str, b: str, value: float | None = None) -> dict:
    return {"kind": kind, "a": a, "b": b, "value": value}


def _num(value: float | int | str | list | tuple | None, joint: dict) -> float:
    if isinstance(value, (list, tuple)):
        raise JointError(f"joint {joint.get('id')!r} value must be a scalar for this type")
    if value is None:
        raise JointError(f"joint {joint.get('id')!r} needs a numeric value")
    return float(value)
