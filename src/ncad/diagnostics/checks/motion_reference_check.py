"""Static reference checks for a motion document (bucket: validation & diagnostics).

The motion doc drives a referenced assembly. Catches: a missing/unresolvable assembly reference, a
driver joint that does not exist or is not drivable (only revolute/slider can be driven), and a
coupling whose primary (between[0]) is not the driven joint (a warning: it just will not be
enforced, 6.2/6.3 rule). The coupling-primary check runs only once the driver joint is itself valid,
so a broken driver does not also spray cascade warnings. Returns Diagnostics; never raises. The
caller supplies the resolved assembly block (or None if the file could not be read). One class.
"""

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic

_DRIVABLE = frozenset({"revolute", "slider"})


class MotionReferenceCheck:
    """Validates the driver + coupling references of a motion document against its assembly."""

    def check(self, document: dict, assembly: dict | None) -> list[Diagnostic]:
        """Return motion reference Diagnostics (empty when the driver + couplings resolve)."""
        motion = document.get("motion") or {}
        out: list[Diagnostic] = []
        if assembly is None:
            out.append(Diagnostic(
                severity="error", code=codes.MOTION_ASSEMBLY_MISSING, location="motion.assembly",
                message=f"assembly {motion.get('assembly')!r} could not be resolved",
                hint="check the motion's 'assembly' path", stage="semantic"))
            return out
        joints = {j.get("id"): j for j in (assembly.get("joints") or [])}
        driver = motion.get("driver") or {}
        driven = driver.get("joint")
        joint = joints.get(driven)
        if joint is None:
            out.append(Diagnostic(
                severity="error", code=codes.DRIVER_JOINT_MISSING, location="motion.driver.joint",
                message=f"driver joint {driven!r} is not a joint in the assembly",
                hint="name a revolute or slider joint declared in the assembly", stage="semantic"))
            return out
        if joint.get("type") not in _DRIVABLE:
            out.append(Diagnostic(
                severity="error", code=codes.DRIVER_JOINT_NOT_DRIVABLE,
                location="motion.driver.joint",
                message=f"driver joint {driven!r} is a {joint.get('type')!r}; only revolute/slider "
                        "can be driven",
                hint="drive a revolute or slider joint", stage="semantic"))
            return out
        for cidx, coupling in enumerate(assembly.get("couplings") or []):
            between = coupling.get("between") or []
            if between and between[0] != driven:
                out.append(Diagnostic(
                    severity="warning", code=codes.COUPLING_PRIMARY_MISMATCH,
                    location=f"assembly.couplings.{cidx}.between.0",
                    message=f"coupling {coupling.get('id')!r} primary {between[0]!r} is not the "
                            f"driven joint {driven!r}; it will not be enforced",
                    hint="set between[0] to the driven joint", stage="semantic"))
        return out
