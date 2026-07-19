"""Per-frame motion-time interference: run the static InterferenceChecker at each trajectory frame.

Reuses the assembly InterferenceChecker (pairwise kernel distance + common volume + classify) over a
motion trajectory's per-frame placements. For each frame it places every watched instance's shape at
that frame's transform and checks the requested pairs, recording only INTERFERING frames as timeline
events {frame, t, a, b, volume}. DISCRETE per-frame sampling: a collision fully between two frames
can be missed (tied to solve resolution); continuous/swept detection is deferred. Optional: the
builder only calls this when the motion `outputs` block declares interference. One class.

Frame placements are row-major 4x4 in METRES; base shapes + kernel.place work in MM, so each frame's
translation row is scaled back to mm before placing.
"""

import logging
from typing import Any

from ncad.assembly.interference_checker import InterferenceChecker

logger = logging.getLogger(__name__)


class MotionInterference:
    """Runs InterferenceChecker per frame and collects interfering-pair timeline events."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._checker = InterferenceChecker(kernel)

    def events(self, pairs: list | None, shapes_by_id: dict, frames: list,
               to_metres: float) -> list[dict]:
        """Timeline events for interfering pairs across ``frames``.

        :param pairs: instance-id pairs (tuples) to watch, or None to check all pairs each frame.
        :param shapes_by_id: instance id -> its base (mm) shape.
        :param frames: the trajectory frames ({t, driver_value, placements} in metres).
        :param to_metres: mm -> metres factor (frame translation / to_metres = mm).
        :return: [{frame, t, a, b, volume}] for interfering pairs only.
        """
        watch = None if pairs is None else {tuple(sorted(p)) for p in pairs}
        out: list[dict] = []
        for index, frame in enumerate(frames):
            placed = self._place_frame(frame, shapes_by_id, to_metres)
            for finding in self._checker.check(placed):
                if finding.get("status") != "interfering":
                    continue
                key = tuple(sorted((finding["a"], finding["b"])))
                if watch is not None and key not in watch:
                    continue
                out.append({"frame": index, "t": frame.get("t"),
                            "a": finding["a"], "b": finding["b"],
                            "volume": finding["volume"]})
        return out

    def _place_frame(self, frame: dict, shapes_by_id: dict, to_metres: float) -> list[dict]:
        """Place each watched shape at this frame's transform (converted metres -> mm)."""
        placed: list[dict] = []
        for iid, matrix_m in frame.get("placements", {}).items():
            shape = shapes_by_id.get(iid)
            if shape is None:
                continue
            placed.append({"id": iid,
                           "shape": self._kernel.place(shape, _to_mm(matrix_m, to_metres))})
        return placed


def _to_mm(matrix_m: list, to_metres: float) -> list:
    """A copy of a row-major 4x4 with the translation row (row 3) scaled metres -> mm."""
    scale = 1.0 / to_metres
    return [row[:] if i < 3 else [row[0] * scale, row[1] * scale, row[2] * scale]
            for i, row in enumerate(matrix_m)]
