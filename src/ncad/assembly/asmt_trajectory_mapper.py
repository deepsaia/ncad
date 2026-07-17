"""Map a pyondsel motion Trajectory back to ncad per-frame instance placements for the sidecar.

The multibody solver returns, per part per frame, a world position (metres) + Bryant (Tait) X-Y-Z
angles. This rebuilds each instance's row-major 4x4 placement (metres, the convention the static
sidecar + viewer use) at each frame, and packages the frames into the <name>.motion.json shape
{t, driver_value, status, placements}. An instance the solver did not move (or that is missing from
the trajectory) keeps its static rest placement. Pure math; one class.
"""

import math
from typing import Any


class AsmtTrajectoryMapper:
    """Turns a pyondsel Trajectory into the motion sidecar's per-frame placement records."""

    def to_frames(self, trajectory: Any, name: str, instances: list[dict], placements_mm: dict,
                  values: list[float], to_metres: float) -> list[dict]:
        """Per-frame records aligned to ``values`` (the driver sweep); placements in metres."""
        rest_metres = {iid: _bake(placements_mm[iid], to_metres) for iid in placements_mm}
        part_paths = {iid: f"/{name}/{iid}" for iid in placements_mm}
        frame_count = min(_trajectory_frames(trajectory, part_paths), len(values))
        span = values[-1] - values[0] if len(values) > 1 else 0.0
        frames: list[dict] = []
        for i in range(frame_count):
            placements = {}
            for iid in placements_mm:
                pose = self._frame_pose(trajectory, part_paths[iid], i)
                placements[iid] = pose if pose is not None else rest_metres[iid]
            value = values[i]
            frames.append({"t": 0.0 if span == 0 else (value - values[0]) / span,
                           "driver_value": value, "status": "solved", "placements": placements})
        return frames

    def _frame_pose(self, trajectory: Any, path: str, i: int) -> list[list[float]] | None:
        """The instance's row-major 4x4 (metres) at frame ``i``, or None if not in trajectory."""
        part = trajectory.parts.get(path)
        if part is None or i >= part.frame_count():
            return None
        px, py, pz = part.positions[i]
        rotation = _rotation_from_bryant(part.bryant_angles[i])
        # Row-major, translation in the last row (matches AssemblyPlacement / BodyPose). Each row is
        # the image of a basis vector, so row i = column i of the standard rotation matrix.
        return [[rotation[0][0], rotation[1][0], rotation[2][0], 0.0],
                [rotation[0][1], rotation[1][1], rotation[2][1], 0.0],
                [rotation[0][2], rotation[1][2], rotation[2][2], 0.0],
                [px, py, pz, 1.0]]


def _trajectory_frames(trajectory: Any, part_paths: dict) -> int:
    """The common frame count across the trajectory's parts (0 if none present)."""
    counts = [trajectory.parts[p].frame_count() for p in part_paths.values()
              if p in trajectory.parts]
    return min(counts) if counts else 0


def _rotation_from_bryant(bryant: tuple) -> list[list[float]]:
    """3x3 rotation from Bryant X-Y-Z angles (intrinsic order): R = Rx(bx) Ry(by) Rz(bz)."""
    bx, by, bz = bryant
    cx, sx = math.cos(bx), math.sin(bx)
    cy, sy = math.cos(by), math.sin(by)
    cz, sz = math.cos(bz), math.sin(bz)
    rx = [[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]]
    ry = [[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]]
    rz = [[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]]
    return _matmul(_matmul(rx, ry), rz)


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)] for r in range(3)]


def _bake(matrix_mm: list[list[float]], to_metres: float) -> list[list[float]]:
    """Copy a row-major placement (mm) with its translation row scaled to metres."""
    out = [row[:] for row in matrix_mm]
    out[3][0] *= to_metres
    out[3][1] *= to_metres
    out[3][2] *= to_metres
    return out
