"""Parse and validate an assembly ``motion`` block into a driven joint + a driver value sweep.

Kinematic only: a driver sweeps ONE joint's free DoF over an even range; the MotionSolver re-solves
the position network at each value. Force dynamics is Phase 14. A malformed block raises
MotionParamError (the builder wraps it into an id-attributed issue).
"""


class MotionParamError(Exception):
    """A motion block's driver is missing or invalid; reported by the builder."""


class MotionDriver:
    """Turns a ``motion`` block into (driven joint id, ordered driver values)."""

    def parse(self, motion: dict) -> tuple[str, list[float]]:
        """Return (driven_joint_id, values); raise MotionParamError on a bad block."""
        driver = motion.get("driver")
        if not isinstance(driver, dict):
            raise MotionParamError("motion needs a 'driver' object")
        joint = driver.get("joint")
        if not isinstance(joint, str) or not joint:
            raise MotionParamError("motion driver needs a 'joint' id")
        if "from" not in driver or "to" not in driver:
            raise MotionParamError("motion driver needs 'from' and 'to'")
        start, end = float(driver["from"]), float(driver["to"])
        steps = driver.get("steps")
        if not isinstance(steps, int) or steps <= 0:
            raise MotionParamError("motion driver needs a positive integer 'steps'")
        if start == end:
            raise MotionParamError("motion driver 'from' and 'to' must differ")
        values = [start + k * (end - start) / steps for k in range(steps + 1)]
        return joint, values
