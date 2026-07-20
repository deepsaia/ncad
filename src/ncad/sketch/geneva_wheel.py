"""Generate a Geneva (Maltese-cross) wheel profile plus its intermittent motion law.

The single source of truth for a Geneva drive, mirroring CamProfile / GearProfile: one object owns
BOTH the drawn slotted star-wheel ``outline()`` AND the wheel-angle law ``wheel_angle(crank)``, so
the drawn slots and the coupled motion agree.

External Geneva, N slots, drive-crank radius ``a``: center distance ``c = a / sin(pi/N)``. A single
engagement per crank revolution, centred at crank angle 180 deg (the pin farthest out, entering a
slot), spanning +/- (90 - 180/N) deg. During engagement the wheel angle is
``beta(alpha) = atan2(sin alpha, c/a - cos alpha)`` (alpha = crank angle from the engagement
centre), indexing the wheel a net ``360/N`` deg; between engagements the wheel DWELLS (held by the
driver's locking disc). The dwell makes the wheel-angle profile piecewise, which OndselSolver's
motion grammar rejects, so ``expression`` fits a truncated FOURIER series to the PERIODIC REMAINDER
(the profile minus its mean index ramp) and re-adds the ramp; the max fit error is logged. 1 class.
"""

import logging
import math

import numpy as np

logger = logging.getLogger(__name__)

_FIT_HARMONICS = 24
_FIT_SAMPLES = 720
_COEFF_FLOOR = 1e-9
_MIN_SLOTS = 3


class GenevaWheelError(Exception):
    """Invalid Geneva parameters (slots < 3, non-positive radius)."""


class GenevaWheel:
    """A Geneva star wheel (N slots) with its intermittent wheel-angle law; one source of truth."""

    def __init__(self, slots: int, crank_radius: float, pin_radius: float = 3.0,
                 slot_clearance: float = 0.4) -> None:
        if not isinstance(slots, int) or slots < _MIN_SLOTS:
            raise GenevaWheelError(f"geneva slots must be an integer >= {_MIN_SLOTS}")
        if not isinstance(crank_radius, (int, float)) or crank_radius <= 0:
            raise GenevaWheelError("geneva crank_radius must be a positive number")
        if not isinstance(pin_radius, (int, float)) or pin_radius <= 0:
            raise GenevaWheelError("geneva pin_radius must be a positive number")
        self._n = int(slots)
        self._a = float(crank_radius)
        self._pin_r = float(pin_radius)
        self._clear = float(slot_clearance)
        self._c = self._a / math.sin(math.pi / self._n)         # center distance
        self._index_deg = 360.0 / self._n                        # wheel rotation per engagement
        # The pin enters/leaves the slot at wheel-local bearing +/- 180/N (= index/2); this is both
        # the wheel_angle zero-offset and the slot phase so a slot faces the pin at rest.
        self._psi_start = 180.0 / self._n

    @property
    def center_distance(self) -> float:
        """Crank axis to wheel axis distance: a / sin(pi/N)."""
        return self._c

    @property
    def wheel_radius(self) -> float:
        """Outer radius of the star wheel (the slot mouth sits at the rim)."""
        # The pin reaches closest to the wheel centre (c - a) at mid-engagement; the rim clears that
        # by a margin so the slot bottom + lobe stay solid.
        return self._c - self._a + self._pin_r * 2.0 + 4.0

    @property
    def engagement_half_angle_deg(self) -> float:
        """Half the crank engagement sweep: 90 - 180/N degrees."""
        return 90.0 - 180.0 / self._n

    def wheel_angle(self, crank_deg: float) -> float:
        """Cumulative wheel rotation (deg) at crank angle ``crank_deg``.

        The wheel indexes once per crank revolution (one engagement centred at local crank 180 deg,
        the pin deepest in a slot): flat (dwell) outside the +/- engagement half-window, the exact
        engagement kinematics inside. For a CCW crank the wheel indexes CW, so the rotation is
        NEGATIVE (decreasing by index = 360/N per revolution). The rotation is the pin's bearing
        from the wheel axis, ``psi(crank) = atan2(a sin, c + a cos)``, offset so it is 0 at the
        engagement start (pin enters the slot at local bearing +180/N). Cumulative across revs.
        """
        revs = math.floor(crank_deg / 360.0)
        local = crank_deg - revs * 360.0                         # 0 .. 360 within this revolution
        base = -revs * self._index_deg                           # CW index per revolution
        half = self.engagement_half_angle_deg
        if local < 180.0 - half:
            return base
        if local > 180.0 + half:
            return base - self._index_deg
        # psi = the pin's bearing from the wheel axis; the slot the pin rides tracks it. Offset by
        # the entry bearing (+180/N) so wheel_angle is 0 at engagement start, -index at the end.
        psi = math.degrees(math.atan2(self._a * math.sin(math.radians(local)),
                                      self._c + self._a * math.cos(math.radians(local))))
        return base + psi - self._psi_start

    def outline(self, rim_arc_samples: int = 16) -> list[list[float]]:
        """The star-wheel outline as a closed [x, y] point list (mm), centred at the wheel axis.

        N convex lobes at the rim separated by N radial slots the pin enters. Each slot is a
        STRAIGHT-WALLED channel (parallel walls a constant half-width apart, = pin_r + clearance),
        cut radially in to a flat bottom, so the round pin clears the walls at every depth (a wedge
        notch would pinch the pin deep in). The slots are PHASED so a slot centre sits at the
        pin-entry bearing (+180/N) at rest, aligned to receive the pin as the engagement begins.

        The boundary is walked CCW, one slot + lobe per period: down the leading wall, across the
        bottom, up the trailing wall, then a convex rim arc to the next slot.
        """
        w = self._pin_r + self._clear                            # slot half-width (parallel walls)
        rim = self.wheel_radius
        bottom_r = max(self._c - self._a - self._pin_r, w + 2.0)  # bottom corner radius (> w)
        t_out = math.sqrt(max(rim * rim - w * w, 0.0))           # wall length at the rim
        t_in = math.sqrt(max(bottom_r * bottom_r - w * w, 0.0))  # wall length at the bottom corner
        wall_rim_ang = math.asin(min(1.0, w / rim))              # rim angle offset of a wall corner
        pitch = 2.0 * math.pi / self._n
        pts: list[list[float]] = []
        for k in range(self._n):
            sc = math.radians(self._psi_start) + k * pitch       # slot centre angle
            u = (math.cos(sc), math.sin(sc))                     # radial (centreline) direction
            v = (-math.sin(sc), math.cos(sc))                    # perpendicular (across the slot)
            # Leading wall: rim corner -> bottom corner (offset -w across the slot).
            pts.append([t_out * u[0] - w * v[0], t_out * u[1] - w * v[1]])
            pts.append([t_in * u[0] - w * v[0], t_in * u[1] - w * v[1]])
            # Bottom, then trailing wall: bottom corner -> rim corner (offset +w).
            pts.append([t_in * u[0] + w * v[0], t_in * u[1] + w * v[1]])
            pts.append([t_out * u[0] + w * v[0], t_out * u[1] + w * v[1]])
            # Convex rim (lobe) arc from this slot's trailing corner to the next slot's leading one.
            start = sc + wall_rim_ang
            end = sc + pitch - wall_rim_ang
            for j in range(1, rim_arc_samples):
                a = start + (end - start) * j / rim_arc_samples
                pts.append([rim * math.cos(a), rim * math.sin(a)])
        return pts

    def expression(self, a0_deg: float, span_deg: float) -> str:
        """The wheel's prescribed ROTATIONAL motion as a smooth function of ``time`` (radians).

        The crank sweeps a0 + span*time (deg) over t in [0, 1]. The wheel profile is not periodic
        (it gains 360/N per rev), so fit the periodic REMAINDER (profile minus the mean index ramp)
        with a truncated Fourier series and re-add the ramp. Max fit error logged.
        """
        thetas = np.arange(_FIT_SAMPLES) * (360.0 / _FIT_SAMPLES)
        wheel = np.array([math.radians(self.wheel_angle(float(t))) for t in thetas])
        # Mean index per crank radian; NEGATIVE (a CCW crank indexes the wheel CW by index/rev).
        ramp_slope = -math.radians(self._index_deg) / (2.0 * math.pi)     # wheel rad per crank rad
        crank_rad = np.radians(thetas)
        remainder = wheel - ramp_slope * crank_rad
        spectrum = np.fft.rfft(remainder)
        max_k = min(_FIT_HARMONICS, len(spectrum) - 1)
        a0_rad = math.radians(a0_deg)
        span_rad = math.radians(span_deg)
        inner = f"({a0_rad} + {span_rad}*time)"
        terms: list[tuple[float, str]] = [
            (float(spectrum[0].real) / _FIT_SAMPLES + ramp_slope * a0_rad, ""),
            (ramp_slope * span_rad, "time"),
        ]
        for k in range(1, max_k + 1):
            ak = 2.0 * float(spectrum[k].real) / _FIT_SAMPLES
            bk = -2.0 * float(spectrum[k].imag) / _FIT_SAMPLES
            if abs(ak) > _COEFF_FLOOR:
                terms.append((ak, f"cos({k}*{inner})"))
            if abs(bk) > _COEFF_FLOOR:
                terms.append((bk, f"sin({k}*{inner})"))
        self._log_fit_error(remainder, spectrum, max_k)
        return _assemble(terms)

    def _log_fit_error(self, remainder: np.ndarray, spectrum: np.ndarray, max_k: int) -> None:
        """Reconstruct the truncated series on the fit grid and log the max error (deg)."""
        recon = np.full(_FIT_SAMPLES, float(spectrum[0].real) / _FIT_SAMPLES)
        theta = np.arange(_FIT_SAMPLES) * (2.0 * math.pi / _FIT_SAMPLES)
        for k in range(1, max_k + 1):
            recon += (2.0 * float(spectrum[k].real) / _FIT_SAMPLES) * np.cos(k * theta)
            recon += (-2.0 * float(spectrum[k].imag) / _FIT_SAMPLES) * np.sin(k * theta)
        err = math.degrees(float(np.max(np.abs(recon - remainder))))
        logger.info("geneva Fourier fit: %d harmonics, max error %.3f deg", max_k, err)


def _assemble(pairs: list[tuple[float, str]]) -> str:
    """Assemble (coefficient, basis) pairs into a signed expression (no '+ -')."""
    out = ""
    for i, (coeff, basis) in enumerate(pairs):
        token = f"{abs(coeff)}" if not basis else f"{abs(coeff)}*{basis}"
        if i == 0:
            out = ("-" + token) if coeff < 0 else token
        else:
            out += (" - " if coeff < 0 else " + ") + token
    return out or "0.0"
