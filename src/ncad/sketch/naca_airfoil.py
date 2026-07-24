"""Generate NACA 4-digit airfoil section points on a unit chord (pure math, no I/O).

The 4-digit family: code MPTT where M = max camber (% chord), P = camber position (tenths of
chord), TT = max thickness (% chord). The section is the mean camber line offset by the
half-thickness distribution normal to the camber line. Points are cosine-spaced (dense at the
leading edge, where curvature is highest) and ordered TE -> upper -> LE -> lower -> TE into one
closed loop the spline interpolates. One class.
"""

import logging
import math

logger = logging.getLogger(__name__)

# Standard NACA 4-digit thickness polynomial coefficients (open trailing edge).
_A0, _A1, _A2, _A3, _A4 = 0.2969, -0.1260, -0.3516, 0.2843, -0.1015


class NacaAirfoil:
    """A NACA 4-digit airfoil section generator on a unit chord."""

    def __init__(self, code: str) -> None:
        if not (isinstance(code, str) and len(code) == 4 and code.isdigit()):
            raise ValueError(f"NACA 4-digit code must be 4 digits; got {code!r}")
        self._m = int(code[0]) / 100.0
        self._p = int(code[1]) / 10.0
        self._t = int(code[2:]) / 100.0

    def points(self, samples: int = 60) -> list[tuple[float, float]]:
        """Return the closed section, TE -> upper -> LE -> lower -> TE, cosine-spaced."""
        xs = _cosine_spacing(samples)
        upper, lower = [], []
        for x in xs:
            yt = self._thickness(x)
            yc, dyc = self._camber(x)
            theta = math.atan(dyc)
            upper.append((x - yt * math.sin(theta), yc + yt * math.cos(theta)))
            lower.append((x + yt * math.sin(theta), yc - yt * math.cos(theta)))
        # TE -> upper (reversed to start at TE) -> LE -> lower -> TE, dropping the duplicated LE.
        loop = list(reversed(upper)) + lower[1:]
        return [(round(x, 9), round(y, 9)) for x, y in loop]

    def _thickness(self, x: float) -> float:
        """Half-thickness at chord fraction ``x`` (standard 4-digit polynomial)."""
        return 5.0 * self._t * (_A0 * math.sqrt(x) + _A1 * x + _A2 * x**2
                                + _A3 * x**3 + _A4 * x**4)

    def _camber(self, x: float) -> tuple[float, float]:
        """The mean camber line height + slope at chord fraction ``x``."""
        if self._m == 0.0 or self._p == 0.0:
            return 0.0, 0.0
        if x < self._p:
            yc = self._m / self._p**2 * (2 * self._p * x - x**2)
            dyc = 2 * self._m / self._p**2 * (self._p - x)
        else:
            yc = self._m / (1 - self._p) ** 2 * ((1 - 2 * self._p) + 2 * self._p * x - x**2)
            dyc = 2 * self._m / (1 - self._p) ** 2 * (self._p - x)
        return yc, dyc


def _cosine_spacing(samples: int) -> list[float]:
    """``samples`` x-stations in [0, 1], clustered at both ends (dense at the LE)."""
    n = max(2, int(samples))
    return [0.5 * (1 - math.cos(math.pi * i / (n - 1))) for i in range(n)]
