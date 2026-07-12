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
        signature = SIGNATURES[jtype]
        value = joint.get("value")
        prims = self._positioning(jtype)
        prims.extend(self._value_pins(jtype, value, joint))
        return prims, signature

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
        if jtype == "revolute":
            return [_p("dirs_angle", "A.secondary", "B.secondary", _num(value, joint))]
        if jtype == "slider":
            return [_p("point_plane_distance", "A.origin", "B.plane", _num(value, joint))]
        if jtype == "point_on_line":
            return [_p("point_plane_distance", "A.origin", "B.plane", _num(value, joint))]
        # cylindrical / planar / ball: multi-DoF value-pinning deferred (see spec section 3).
        logger.debug("value-pinning for %r is deferred in 5.4a; leaving DoF free", jtype)
        return []


def _p(kind: str, a: str, b: str, value: float | None = None) -> dict:
    return {"kind": kind, "a": a, "b": b, "value": value}


def _num(value: float | int | str | list | tuple | None, joint: dict) -> float:
    if isinstance(value, (list, tuple)):
        raise JointError(f"joint {joint.get('id')!r} value must be a scalar for this type")
    if value is None:
        raise JointError(f"joint {joint.get('id')!r} needs a numeric value")
    return float(value)
