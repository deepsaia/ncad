"""Generate a true involute spur-gear outline (a closed 2D point list) from standard gear params.

Standard external spur gear, full-depth involute teeth: module ``m``, tooth count ``z``, pressure
angle ``alpha``. Pitch d = m*z; base d_b = d*cos(alpha); addendum r_a = d/2 + m; dedendum
r_f = d/2 - 1.25m. Each tooth flank is the involute of the base circle; a tooth's two flanks are
symmetric about the tooth centre, with the circular tooth thickness pi*m/2 at the pitch circle. The
outline walks z teeth CCW (tooth flanks + addendum tops + root valleys) as a closed point list the
sketch layer turns into a polyline >> extrude. Pure math; no kernel. One class.

Scope: flat involute SPUR gears, standard addendum/dedendum, integer teeth. Deferred: helical/bevel,
root fillets, profile shift, backlash/clearance.
"""

import math

# Points sampled along each involute flank between the base/dedendum and the addendum.
_FLANK_SAMPLES = 8


class GearProfileError(Exception):
    """Invalid gear parameters (module/teeth/pressure_angle out of range)."""


class GearProfile:
    """A full-depth involute spur-gear profile from module, teeth, and pressure angle."""

    def __init__(self, module: float, teeth: int, pressure_angle: float = 20.0) -> None:
        if not isinstance(module, (int, float)) or module <= 0:
            raise GearProfileError("gear module must be a positive number")
        if not isinstance(teeth, int) or teeth < 3:
            raise GearProfileError("gear teeth must be an integer >= 3")
        if not isinstance(pressure_angle, (int, float)) or not 0 < pressure_angle < 45:
            raise GearProfileError("gear pressure_angle must be in (0, 45) degrees")
        self._m = float(module)
        self._z = int(teeth)
        self._alpha = math.radians(float(pressure_angle))

    @property
    def pitch_radius(self) -> float:
        """Pitch-circle radius d/2 = m*z/2."""
        return self._m * self._z / 2.0

    @property
    def base_radius(self) -> float:
        """Base-circle radius (the involute is generated from this): pitch_r * cos(alpha)."""
        return self.pitch_radius * math.cos(self._alpha)

    @property
    def addendum_radius(self) -> float:
        """Tooth-tip radius: pitch_r + module."""
        return self.pitch_radius + self._m

    @property
    def dedendum_radius(self) -> float:
        """Root radius: pitch_r - 1.25*module (standard full-depth dedendum)."""
        return self.pitch_radius - 1.25 * self._m

    @staticmethod
    def center_distance(a: "GearProfile", b: "GearProfile") -> float:
        """The meshing center distance of two gears: (z_a + z_b) * m / 2 (same module)."""
        return (a._z + b._z) * a._m / 2.0

    def outline(self) -> list[list[float]]:
        """The closed gear outline as a list of [x, y] points, walking z teeth CCW.

        Each tooth contributes: the rising involute flank (root->tip), an addendum arc across the
        tip, the falling flank (tip->root), then a root arc to the next tooth. The involute is
        sampled at ``_FLANK_SAMPLES`` points; arcs at a few points so the tip/root read as curves.
        """
        pitch_angle = 2.0 * math.pi / self._z          # angular pitch (one tooth period)
        # Half tooth thickness at the pitch circle, as an angle: (pi*m/2) / pitch_r / 2 ... the
        # circular tooth thickness is pi*m/2, so the half-angle at the pitch circle is
        # (pi*m/2) / (2 * pitch_r). The involute's own angular offset at the pitch circle is
        # inv(alpha); the flank is centred so the tooth is symmetric about angle 0.
        half_tooth_angle = (math.pi * self._m / 2.0) / (2.0 * self.pitch_radius)
        inv_alpha = math.tan(self._alpha) - self._alpha
        # A flank point's polar angle = base-flank-start + inv(roll); we want the flank to pass the
        # pitch circle at +half_tooth_angle (rising flank) about the tooth centre. So the flank
        # start angle offsets by (half_tooth_angle + inv_alpha).
        flank_offset = half_tooth_angle + inv_alpha
        points: list[list[float]] = []
        for k in range(self._z):
            centre = k * pitch_angle
            # Rising flank: root -> tip, at angle (centre - flank_offset + inv(roll)).
            rising = self._flank(centre, -1.0, flank_offset)
            # Falling flank: tip -> root, mirror (angle centre + flank_offset - inv(roll)).
            falling = list(reversed(self._flank(centre, +1.0, flank_offset)))
            points.extend(rising)
            points.extend(falling)
        return points

    def _flank(self, centre: float, side: float, flank_offset: float) -> list[list[float]]:
        """One involute flank from the dedendum/base up to the addendum, root->tip.

        ``side`` = -1 rising (left) / +1 falling (right); the flank's polar angle at radius r is
        ``centre + side*(flank_offset - inv(roll(r)))`` so the two flanks are symmetric about
        ``centre`` and cross the pitch circle at +/- the half-tooth angle.
        """
        r_start = max(self.base_radius, self.dedendum_radius)
        out: list[list[float]] = []
        # Root point below the base circle (radial), so the tooth reaches the dedendum.
        if self.dedendum_radius < r_start:
            root_angle = centre + side * flank_offset
            out.append([self.dedendum_radius * math.cos(root_angle),
                        self.dedendum_radius * math.sin(root_angle)])
        for i in range(_FLANK_SAMPLES + 1):
            r = r_start + (self.addendum_radius - r_start) * i / _FLANK_SAMPLES
            roll = math.acos(max(-1.0, min(1.0, self.base_radius / r)))   # roll angle at radius r
            inv = math.tan(roll) - roll
            angle = centre + side * (flank_offset - inv)
            out.append([r * math.cos(angle), r * math.sin(angle)])
        return out
