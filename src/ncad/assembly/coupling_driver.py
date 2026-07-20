"""Turn a rate-ratio coupling (gear / belt / rack_pinion) into a secondary prescribed-motion spec.

A coupling relates two joints by a ratio; enforcement drives the primary joint and prescribes the
coupled (derived) joint's motion by the ratio (a coupled joint driven as a function of another DoF).
OndselSolver has no gear constraint, so ncad emits the coupled joint as its own prescribed motion
whose expression is ratio x the primary's linear ramp:

- gear:        coupled ANGLE = -ratio x primary_angle  (external mesh reverses sense).
- belt:        coupled ANGLE = +ratio x primary_angle  (same sense).
- rack_pinion: coupled SLIDE = travel(mm/rad) x primary_angle(rad)  (rotation -> translation).

The ratio comes from ONE of two sources, in this order:
1. a ``gears`` block ``{driver: {module, teeth, ...}, driven: {module, teeth, ...}}`` - the ratio
   is derived from GearProfile (mesh_ratio, signed for external/internal; the pinion pitch radius
   for rack_pinion), so the SAME generator that draws the teeth defines the motion (one source of
   truth, like the cam profile); OR
2. an explicit ``ratio`` (z_primary/z_coupled for gear/belt; pinion pitch radius mm/rad for
   rack_pinion) when no ``gears`` block is given.

The primary must drive the coupling's FIRST ``between`` joint; the SECOND is the derived one. The
expression is built in the ASMT motion's own units (radians for rotational, metres for
translational), as a function of ``time`` matching the primary's ramp. Pure; one class.
"""

import math

from ncad.sketch.gear_profile import GearProfile, GearProfileError
from ncad.sketch.geneva_wheel import GenevaWheel, GenevaWheelError

_RATIO_TYPES = frozenset({"gear", "belt", "rack_pinion"})
# Slot / intermittent laws (bucket 6.3): the derived joint follows a closed-form of the crank angle,
# not a constant ratio. scotch_yoke -> a slider = A*sin; geneva -> a revolute = its Fourier-fit law.
_SLOT_TYPES = frozenset({"scotch_yoke", "geneva"})


class CouplingDriverError(Exception):
    """A coupling cannot be enforced as a derived driver; reported as an id-attributed issue."""


class CouplingDriver:
    """Builds the coupled joint's prescribed-motion spec from a rate-ratio coupling + the driver."""

    def secondary(self, coupling: dict, primary: dict) -> dict:
        """Return {joint_id, joint_type, expression} for the coupling's derived joint.

        :param coupling: {id, type, between:[primary_joint, derived_joint], ratio | gears}.
        :param primary: the driver {joint_id, joint_type, start, end} (degrees for a revolute).
        :raises CouplingDriverError: on an unknown type, bad ratio/gears, or a primary that does
            not drive the coupling's first joint.
        """
        ctype = coupling.get("type")
        if ctype not in _RATIO_TYPES and ctype not in _SLOT_TYPES:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} type {ctype!r} is not an enforceable coupling")
        between = coupling.get("between") or []
        if len(between) < 2:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} needs two joints in 'between'")
        if between[0] != primary.get("joint_id"):
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} primary joint {between[0]!r} is not the one the "
                f"driver drives ({primary.get('joint_id')!r})")
        derived_joint = between[1]
        if ctype == "scotch_yoke":
            return self._scotch_yoke(coupling, derived_joint, primary)
        if ctype == "geneva":
            return self._geneva(coupling, derived_joint, primary)
        # The primary ramp in radians: a0 + span*time (the driver sweeps degrees over t 0..1).
        a0 = math.radians(float(primary["start"]))
        span = math.radians(float(primary["end"]) - float(primary["start"]))
        ramp = f"({a0} + {span}*time)"
        if ctype == "rack_pinion":
            # coupled slide (metres) = travel(mm/rad) * primary_angle(rad) / 1000.
            coef = self._rack_travel_mm_per_rad(coupling) / 1000.0
            return {"joint_id": derived_joint, "joint_type": "slider",
                    "expression": f"{coef} * {ramp}"}
        # gear/belt: a signed rotational ratio (external mesh reverses sense; internal/belt keep).
        coef = self._angular_ratio(coupling, reverses=(ctype == "gear"))
        return {"joint_id": derived_joint, "joint_type": "revolute",
                "expression": f"{coef} * {ramp}"}

    def _scotch_yoke(self, coupling: dict, derived_joint: str, primary: dict) -> dict:
        """A scotch yoke: the yoke slide = amplitude * sin(primary_angle), in metres.

        The crank pin rides a slot in the yoke; the yoke's horizontal slide is the pure sinusoid
        A*sin(theta), a smooth ASMT translational expression (no Fourier fit needed).
        """
        amplitude = coupling.get("amplitude")
        if not isinstance(amplitude, (int, float)) or amplitude <= 0:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} needs a positive 'amplitude' (mm)")
        a0 = math.radians(float(primary["start"]))
        span = math.radians(float(primary["end"]) - float(primary["start"]))
        amp_m = float(amplitude) / 1000.0
        return {"joint_id": derived_joint, "joint_type": "slider",
                "expression": f"{amp_m} * sin({a0} + {span}*time)"}

    def _geneva(self, coupling: dict, derived_joint: str, primary: dict) -> dict:
        """A Geneva drive: the wheel rotation from GenevaWheel's Fourier-fit intermittent law."""
        spec = coupling.get("geneva") or {}
        try:
            wheel = GenevaWheel(slots=int(spec["slots"]),
                                crank_radius=float(spec["crank_radius"]))
        except (KeyError, TypeError, GenevaWheelError) as exc:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} 'geneva' block is malformed: {exc}") from exc
        span = float(primary["end"]) - float(primary["start"])
        return {"joint_id": derived_joint, "joint_type": "revolute",
                "expression": wheel.expression(float(primary["start"]), span)}

    def _angular_ratio(self, coupling: dict, reverses: bool) -> float:
        """The signed angular ratio (omega_derived / omega_driver) for a gear/belt coupling.

        From a ``gears`` block: GearProfile.mesh_ratio, already signed (external <0, internal >0).
        From an explicit ``ratio``: a gear reverses sense (-ratio), a belt keeps it (+ratio).
        """
        gears = coupling.get("gears")
        if gears is not None:
            driver, driven = self._gear_pair(coupling, gears)
            return GearProfile.mesh_ratio(driver, driven)
        ratio = self._explicit_ratio(coupling)
        return -ratio if reverses else ratio

    def _rack_travel_mm_per_rad(self, coupling: dict) -> float:
        """The rack's linear travel per radian of pinion rotation (mm/rad).

        From a ``gears`` block: the pinion (``driver``) pitch radius. From an explicit ``ratio``:
        the ratio value taken directly as mm/rad.
        """
        gears = coupling.get("gears")
        if gears is not None:
            driver, _ = self._gear_pair(coupling, gears)
            return driver.rack_travel_per_radian()
        return self._explicit_ratio(coupling)

    def _gear_pair(self, coupling: dict, gears: dict) -> tuple[GearProfile, GearProfile]:
        """Build the (driver, driven) GearProfile pair from a coupling ``gears`` block."""
        try:
            driver = GearProfile(**gears["driver"])
            driven = GearProfile(**gears["driven"])
        except (KeyError, TypeError, GearProfileError) as exc:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} 'gears' block is malformed: {exc}") from exc
        return driver, driven

    def _explicit_ratio(self, coupling: dict) -> float:
        """The explicit positive ``ratio`` field, or raise if missing/non-positive."""
        ratio = coupling.get("ratio")
        if not isinstance(ratio, (int, float)) or ratio <= 0:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} needs a positive 'ratio' or a 'gears' block")
        return float(ratio)
