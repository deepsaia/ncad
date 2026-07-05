"""A 2D affine transform for sketch-modify operations.

Holds the six numbers of a 2x3 affine map (x' = a*x + b*y + c; y' = d*x + e*y + f)
plus a scalar radius factor, so a circle/arc radius transforms consistently with the
positions. Constructed via named classmethods (translation/rotation/scaling/reflection)
so callers express intent, not matrix entries.
"""

import math


class AffineTransform:
    """A 2D affine map applied to sketch point positions and curve radii."""

    def __init__(self, a: float, b: float, c: float, d: float, e: float, f: float,
                 radius_factor: float) -> None:
        self._a, self._b, self._c = a, b, c
        self._d, self._e, self._f = d, e, f
        self._radius_factor = radius_factor

    @classmethod
    def translation(cls, dx: float, dy: float) -> "AffineTransform":
        """Translate by (dx, dy)."""
        return cls(1.0, 0.0, dx, 0.0, 1.0, dy, 1.0)

    @classmethod
    def rotation(cls, cx: float, cy: float, degrees: float) -> "AffineTransform":
        """Rotate CCW by ``degrees`` about (cx, cy)."""
        theta = math.radians(degrees)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        c = cx - cx * cos_t + cy * sin_t
        f = cy - cx * sin_t - cy * cos_t
        return cls(cos_t, -sin_t, c, sin_t, cos_t, f, 1.0)

    @classmethod
    def scaling(cls, cx: float, cy: float, factor: float) -> "AffineTransform":
        """Uniformly scale by ``factor`` about (cx, cy)."""
        c = cx - cx * factor
        f = cy - cy * factor
        return cls(factor, 0.0, c, 0.0, factor, f, abs(factor))

    @classmethod
    def reflection(cls, ax: float, ay: float, bx: float, by: float) -> "AffineTransform":
        """Reflect across the line through (ax, ay) and (bx, by)."""
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        cos_2t = (dx * dx - dy * dy) / denom
        sin_2t = 2.0 * dx * dy / denom
        c = ax - ax * cos_2t - ay * sin_2t
        f = ay - ax * sin_2t + ay * cos_2t
        return cls(cos_2t, sin_2t, c, sin_2t, -cos_2t, f, 1.0)

    def apply_point(self, x: float, y: float) -> tuple[float, float]:
        """Map a point through the affine transform."""
        return (self._a * x + self._b * y + self._c,
                self._d * x + self._e * y + self._f)

    @property
    def radius_factor(self) -> float:
        """The factor to scale a circle/arc radius by (1.0 except for scaling)."""
        return self._radius_factor
