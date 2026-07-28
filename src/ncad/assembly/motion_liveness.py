"""Detect a motion solve that produced NO movement (a frozen-but-'solved' trajectory).

Every frame the mapper writes carries ``status = "solved"`` even when the solver returned identical
poses on every frame (a degenerate co-solve, an over-constrained loop, a coupling the solver
silently dropped). Such a trajectory is indistinguishable from a real one without comparing per-body
poses, so a user believes a mechanism animated when it did not. This checker compares each
non-grounded instance's placement across the frames and reports the ones that never move; the
builder turns a fully-frozen result (nothing but the grounded bodies moved) into a loud warning + an
issue instead of a silent success. Pure over the frame records; one class.
"""


class MotionLivenessChecker:
    """Reports which instances actually move across a trajectory's frames (frozen detection)."""

    def assess(self, frames: list[dict], ground_ids: set[str], tol_m: float = 1e-7) -> dict:
        """Assess whether the trajectory shows real movement.

        :param frames: the ``motion.json`` frame records (each ``{placements: {iid: 4x4}}``, m).
        :param ground_ids: instance ids that are grounded (expected not to move; excluded from the
            "should have moved" set).
        :param tol_m: per-component movement threshold (metres) below which a body is "not moving".
        :return: ``{"any_moved": bool, "moved": [iid...], "frozen": [iid...], "movable": int,
            "frame_count": int}`` where ``movable`` is the count of non-grounded instances and
            ``frozen`` lists movable instances whose placement never changed beyond ``tol_m``.
        """
        if len(frames) < 2:
            # a single frame (or none) cannot show movement; treat as not-assessable, not frozen.
            return {"any_moved": False, "moved": [], "frozen": [], "movable": 0,
                    "frame_count": len(frames)}
        first = frames[0].get("placements", {})
        moved: list[str] = []
        frozen: list[str] = []
        for iid, start in first.items():
            if iid in ground_ids:
                continue
            # A body moves if it differs from its rest pose at ANY frame, not just the last: a
            # full-cycle driver (0..360) returns every body to its start, so a first-vs-last check
            # would call a genuinely-spinning mechanism frozen. Scan the whole trajectory.
            if _moved_any_frame(frames, iid, start, tol_m):
                moved.append(iid)
            else:
                frozen.append(iid)
        return {"any_moved": bool(moved), "moved": sorted(moved), "frozen": sorted(frozen),
                "movable": len(moved) + len(frozen), "frame_count": len(frames)}


def _moved_any_frame(frames: list[dict], iid: str, rest: list[list[float]], tol_m: float) -> bool:
    """Whether ``iid`` departs from its ``rest`` pose beyond ``tol_m`` at any frame in the sweep.

    Scans the full trajectory (not just the last frame) so a full-revolution driver, which returns
    every body to its start pose, is not mistaken for a frozen mechanism.
    """
    for frame in frames:
        pose = frame.get("placements", {}).get(iid)
        if pose is not None and _pose_changed(rest, pose, tol_m):
            return True
    return False


def _pose_changed(a: list[list[float]], b: list[list[float]], tol_m: float) -> bool:
    """Whether two row-major 4x4 placements differ beyond ``tol_m`` in any element.

    Compares the full 4x4 (rotation rows + translation row), so a body that only rotates in place
    (translation unchanged) still counts as moved. tol is a plain elementwise bound: rotation
    entries are unitless in [-1, 1] and translation is in metres, so a shared small tol separates
    numeric noise from real motion at both.
    """
    for i in range(4):
        for j in range(4):
            if abs(a[i][j] - b[i][j]) > tol_m:
                return True
    return False
