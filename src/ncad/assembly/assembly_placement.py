"""Resolve an instance placement (position + rotation) to a row-major 4x4 rigid matrix.

Reuses the transform vocabulary (position translate + axis-angle or euler rotation) so the frame
convention matches the ``transform`` op / ``kernel.transform``, and is exactly the form the Phase
5.2 solver will output. Convention: rotation about the origin is applied first, then translation;
the matrix is ROW-MAJOR with the translation in the last row (the viewer transposes into three.js
column-major). Pure math, deterministic.
"""

import math
from typing import Any

_IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
             [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


class AssemblyPlacement:
    """Computes the 4x4 rigid matrix for an instance placement."""

    def matrix(self, placement: dict | None) -> list[list[float]]:
        """Return the row-major 4x4 for ``placement``; None/empty is identity."""
        if not placement:
            return [row[:] for row in _IDENTITY]
        rot = self._rotation(placement.get("rotation"))
        position = placement.get("position") or [0.0, 0.0, 0.0]
        px, py, pz = float(position[0]), float(position[1]), float(position[2])
        # Row-major: rotation 3x3 in the top-left, translation in the last row.
        return [
            [rot[0][0], rot[0][1], rot[0][2], 0.0],
            [rot[1][0], rot[1][1], rot[1][2], 0.0],
            [rot[2][0], rot[2][1], rot[2][2], 0.0],
            [px, py, pz, 1.0],
        ]

    def _rotation(self, rotation: Any) -> list[list[float]]:
        if not rotation:
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        if "euler" in rotation:
            rx, ry, rz = (math.radians(a) for a in rotation["euler"])
            # Fixed XYZ order: Rz @ Ry @ Rx (documented convention).
            return _mul3(_mul3(_rot_axis((0.0, 0.0, 1.0), rz), _rot_axis((0.0, 1.0, 0.0), ry)),
                         _rot_axis((1.0, 0.0, 0.0), rx))
        axis = rotation.get("axis", [0.0, 0.0, 1.0])
        angle = math.radians(float(rotation.get("angle", 0.0)))
        return _rot_axis(axis, angle)


def _rot_axis(axis: Any, angle: float) -> list[list[float]]:
    """Rodrigues rotation matrix (3x3) about a (possibly unnormalized) axis by ``angle`` rad."""
    ax, ay, az = float(axis[0]), float(axis[1]), float(axis[2])
    norm = math.sqrt(ax * ax + ay * ay + az * az)
    if norm < 1e-12:
        return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    ax, ay, az = ax / norm, ay / norm, az / norm
    c, s, t = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return [
        [t * ax * ax + c, t * ax * ay - s * az, t * ax * az + s * ay],
        [t * ax * ay + s * az, t * ay * ay + c, t * ay * az - s * ax],
        [t * ax * az - s * ay, t * ay * az + s * ax, t * az * az + c],
    ]


def _mul3(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """3x3 matrix product ``a @ b``."""
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
