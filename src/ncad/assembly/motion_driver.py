"""Parse and validate an assembly ``motion`` block into a driven joint + a driver value sweep.

Kinematic only: a driver sweeps ONE joint's free DoF over an even range; the MotionSolver re-solves
the position network at each value. Force dynamics is deferred to the physics-engine backend
(Phase 17). A malformed block raises MotionParamError (the builder wraps it into an id-attributed
issue).
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
        steps = _resolve_steps(driver)
        if start == end:
            raise MotionParamError("motion driver 'from' and 'to' must differ")
        values = [start + k * (end - start) / steps for k in range(steps + 1)]
        return joint, values


def _resolve_steps(driver: dict) -> int:
    """The solve-frame count: explicit ``steps`` if given, else ``round(fps * duration)``.

    ``steps`` is the number of solve intervals over the sweep (the smoothness knob; N steps yield
    N+1 inclusive frames). It is authored data, not a real-time rate - a mechanism that needs to
    catch fast engagement (Geneva, cam) raises it. As a convenience, a motion can instead declare
    ``fps`` + ``duration`` (seconds) and the frame count is derived, so authors can think in
    playback terms; an explicit ``steps`` always wins. Playback SPEED is a separate viewer concern.
    """
    steps = driver.get("steps")
    if steps is not None:
        if not isinstance(steps, int) or steps <= 0:
            raise MotionParamError("motion driver needs a positive integer 'steps'")
        return steps
    fps, duration = driver.get("fps"), driver.get("duration")
    if fps is None and duration is None:
        raise MotionParamError("motion driver needs 'steps' (or 'fps' + 'duration')")
    if fps is None or duration is None:
        raise MotionParamError("motion driver 'fps' and 'duration' must be given together")
    if not isinstance(fps, (int, float)) or fps <= 0:
        raise MotionParamError("motion driver 'fps' must be a positive number")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise MotionParamError("motion driver 'duration' must be a positive number")
    derived = round(fps * duration)
    if derived <= 0:
        raise MotionParamError("motion driver 'fps' * 'duration' must yield at least 1 step")
    return derived
