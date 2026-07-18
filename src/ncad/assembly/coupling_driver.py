"""Turn a rate-ratio coupling (gear / belt / rack_pinion) into a secondary prescribed-motion spec.

A coupling relates two joints by a ratio; enforcement drives the primary joint and prescribes the
coupled (derived) joint's motion by the ratio (design section 8, FK "a function of another DoF").
OndselSolver has no gear constraint, so ncad emits the coupled joint as its own prescribed motion
whose expression is ratio x the primary's linear ramp:

- gear:        coupled ANGLE = -ratio x primary_angle  (external mesh reverses sense).
- belt:        coupled ANGLE = +ratio x primary_angle  (same sense).
- rack_pinion: coupled SLIDE = ratio(mm/rad) x primary_angle(rad)  (rotation -> translation).

``ratio`` = z_primary / z_coupled for gear/belt; the pinion pitch radius (mm/rad) for rack_pinion.
The primary must drive the coupling's FIRST ``between`` joint; the SECOND is the derived one. The
expression is built in the ASMT motion's own units (radians for rotational, metres for
translational), as a function of ``time`` matching the primary's ramp. Pure; one class.
"""

import math

_RATIO_TYPES = frozenset({"gear", "belt", "rack_pinion"})


class CouplingDriverError(Exception):
    """A coupling cannot be enforced as a derived driver; reported as an id-attributed issue."""


class CouplingDriver:
    """Builds the coupled joint's prescribed-motion spec from a rate-ratio coupling + the driver."""

    def secondary(self, coupling: dict, primary: dict) -> dict:
        """Return {joint_id, joint_type, expression} for the coupling's derived joint.

        :param coupling: {id, type, between:[primary_joint, derived_joint], ratio}.
        :param primary: the driver {joint_id, joint_type, start, end} (degrees for a revolute).
        :raises CouplingDriverError: on an unknown type, non-positive ratio, or a primary that does
            not drive the coupling's first joint.
        """
        ctype = coupling.get("type")
        if ctype not in _RATIO_TYPES:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} type {ctype!r} is not a rate-ratio coupling")
        between = coupling.get("between") or []
        if len(between) < 2:
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} needs two joints in 'between'")
        if between[0] != primary.get("joint_id"):
            raise CouplingDriverError(
                f"coupling {coupling.get('id')!r} primary joint {between[0]!r} is not the one the "
                f"driver drives ({primary.get('joint_id')!r})")
        ratio = coupling.get("ratio")
        if not isinstance(ratio, (int, float)) or ratio <= 0:
            raise CouplingDriverError(f"coupling {coupling.get('id')!r} needs a positive 'ratio'")
        derived_joint = between[1]
        # The primary ramp in radians: a0 + span*time (the driver sweeps degrees over t 0..1).
        a0 = math.radians(float(primary["start"]))
        span = math.radians(float(primary["end"]) - float(primary["start"]))
        ramp = f"({a0} + {span}*time)"
        if ctype == "rack_pinion":
            # coupled slide (metres) = ratio(mm/rad) * primary_angle(rad) / 1000.
            coef = float(ratio) / 1000.0
            return {"joint_id": derived_joint, "joint_type": "slider",
                    "expression": f"{coef} * {ramp}"}
        # gear reverses sense (-ratio); belt keeps it (+ratio). Rotational, radians.
        coef = (-float(ratio)) if ctype == "gear" else float(ratio)
        return {"joint_id": derived_joint, "joint_type": "revolute",
                "expression": f"{coef} * {ramp}"}
