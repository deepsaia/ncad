"""Build a row-major 4x4 rigid matrix from a py-slvs solved pose (translate + quaternion).

py-slvs solves each movable body as a transform whose translate (dx,dy,dz) and unit quaternion
(qw,qx,qy,qz) are the unknowns; this converts that solved pose to the same row-major 4x4 (mm,
translation in the last row) AssemblyPlacement emits, so the viewer consumes it unchanged.
Pure math.
"""

import math


class BodyPose:
    """Converts a solved (translate, quaternion) pose to a row-major 4x4."""

    def matrix(self, translate: tuple, quaternion: tuple) -> list[list[float]]:
        """Return the row-major 4x4 for ``translate`` (mm) + unit ``quaternion`` (qw,qx,qy,qz)."""
        qw, qx, qy, qz = quaternion
        n = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
        if n < 1e-12:
            qw, qx, qy, qz = 1.0, 0.0, 0.0, 0.0
        else:
            qw, qx, qy, qz = qw / n, qx / n, qy / n, qz / n
        # Rotation 3x3 from the unit quaternion. Row-major so that a row-vector point p maps as
        # p' = p . R + t (the AssemblyPlacement / FrameSnap convention), hence rows are the images
        # of the basis vectors: row i = R applied to e_i.
        r = [
            [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy + qw * qz), 2 * (qx * qz - qw * qy)],
            [2 * (qx * qy - qw * qz), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz + qw * qx)],
            [2 * (qx * qz + qw * qy), 2 * (qy * qz - qw * qx), 1 - 2 * (qx * qx + qy * qy)],
        ]
        tx, ty, tz = translate
        return [
            [r[0][0], r[0][1], r[0][2], 0.0],
            [r[1][0], r[1][1], r[1][2], 0.0],
            [r[2][0], r[2][1], r[2][2], 0.0],
            [float(tx), float(ty), float(tz), 1.0],
        ]
