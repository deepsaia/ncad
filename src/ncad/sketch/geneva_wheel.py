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

        The wheel indexes once per crank revolution (one engagement centred at local crank 180 deg):
        flat (dwell) outside the +/- engagement half-window, the exact engagement kinematics inside.
        Cumulative across revolutions, so a multi-rev sweep keeps advancing (base + partial); the
        end of each revolution holds the completed index (crank 360 deg -> a full index, not 0).
        """
        revs = math.floor(crank_deg / 360.0)
        local = crank_deg - revs * 360.0                         # 0 .. 360 within this revolution
        base = revs * self._index_deg
        half = self.engagement_half_angle_deg
        if local < 180.0 - half:
            return base
        if local > 180.0 + half:
            return base + self._index_deg
        alpha = math.radians(local - 180.0)                      # from the engagement centre
        ratio = self._c / self._a
        beta = math.atan2(math.sin(alpha), ratio - math.cos(alpha))   # -index/2 .. +index/2 (rad)
        return base + self._index_deg / 2.0 + math.degrees(beta)

    def outline(self, samples: int = 240) -> list[list[float]]:
        """The star-wheel outline as a closed [x, y] point list (mm), centred at the wheel axis.

        N convex lobes at the rim separated by N radial slots (open channels the pin enters). Each
        slot is a straight-sided notch cut radially to a depth so the pin bottoms at mid-engagement.
        Approximated as a sampled polar profile: the radius drops to the slot bottom within a slot's
        angular half-width, else sits at the rim.
        """
        slot_half = self._pin_r + self._clear
        rim = self.wheel_radius
        slot_bottom = max(self._c - self._a - self._pin_r, rim * 0.2)
        slot_ang_half = math.asin(min(1.0, slot_half / max(rim, 1e-6)))   # slot angular half-width
        pts: list[list[float]] = []
        for i in range(samples):
            phi = 2.0 * math.pi * i / samples
            k = round(phi / (2.0 * math.pi / self._n))            # nearest slot centre index
            slot_centre = k * (2.0 * math.pi / self._n)
            r = slot_bottom if abs(_wrap(phi - slot_centre)) < slot_ang_half else rim
            pts.append([r * math.cos(phi), r * math.sin(phi)])
        return pts

    def expression(self, a0_deg: float, span_deg: float) -> str:
        """The wheel's prescribed ROTATIONAL motion as a smooth function of ``time`` (radians).

        The crank sweeps a0 + span*time (deg) over t in [0, 1]. The wheel profile is not periodic
        (it gains 360/N per rev), so fit the periodic REMAINDER (profile minus the mean index ramp)
        with a truncated Fourier series and re-add the ramp. Max fit error logged.
        """
        thetas = np.arange(_FIT_SAMPLES) * (360.0 / _FIT_SAMPLES)
        wheel = np.array([math.radians(self.wheel_angle(float(t))) for t in thetas])
        ramp_slope = math.radians(self._index_deg) / (2.0 * math.pi)      # wheel rad per crank rad
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


def _wrap(angle: float) -> float:
    """Wrap an angle (radians) to [-pi, pi]."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


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
