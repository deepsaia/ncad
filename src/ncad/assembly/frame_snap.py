"""Compute the one-shot rigid transform that lands a moving connector frame on a target frame.

A full frame coincidence: after the transform the moving frame's origin and triad equal the
target's (no free spin, which is why connectors carry a full triad). With the row-vector
convention p' = p . R + t, each moving axis row must map to the target axis, so for orthonormal
frames R = M_moving^T . M_target (R[i][j] = sum_k M[k][i] * T[k][j]). ``flip`` opposes the primary
(Z) axis so two faces seat face-to-face; ``offset`` gaps along the target Z after seating.
Row-major 4x4 (translation in the last row), matching AssemblyPlacement. Pure math.
"""

from ncad.assembly.connector_frame import Vec, _scale, _sub


class FrameSnap:
    """Rigid transform landing one connector frame onto another."""

    def transform(self, moving, target, offset: float = 0.0,
                  flip: bool = False) -> list[list[float]]:
        """Return the row-major 4x4 mapping the moving frame onto the target frame."""
        tx, ty, tz = target.x, target.y, target.z
        if flip:
            # Oppose the primary axis so mating faces seat face-to-face; flip X too to keep a
            # right-handed triad (Y = Z cross X is preserved).
            tz = _scale(tz, -1.0)
            tx = _scale(tx, -1.0)
        mx, my, mz = moving.x, moving.y, moving.z
        # R = M_moving^T . T_target: R[i][j] = mx[i]*tx[j] + my[i]*ty[j] + mz[i]*tz[j].
        r = [[mx[i] * tx[j] + my[i] * ty[j] + mz[i] * tz[j] for j in range(3)] for i in range(3)]
        # Translation: seated target origin (offset along target Z) minus the R-rotated moving
        # origin, so the moving origin maps exactly onto the seated target origin.
        seated: Vec = (target.origin[0] + offset * tz[0], target.origin[1] + offset * tz[1],
                       target.origin[2] + offset * tz[2])
        mo = moving.origin
        rotated: Vec = (mo[0] * r[0][0] + mo[1] * r[1][0] + mo[2] * r[2][0],
                        mo[0] * r[0][1] + mo[1] * r[1][1] + mo[2] * r[2][1],
                        mo[0] * r[0][2] + mo[1] * r[1][2] + mo[2] * r[2][2])
        t = _sub(seated, rotated)
        return [
            [r[0][0], r[0][1], r[0][2], 0.0],
            [r[1][0], r[1][1], r[1][2], 0.0],
            [r[2][0], r[2][1], r[2][2], 0.0],
            [t[0], t[1], t[2], 1.0],
        ]
