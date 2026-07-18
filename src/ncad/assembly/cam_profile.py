"""A general cam profile: the follower lift (displacement) as a function of cam angle.

A cam coupling drives a translating follower by a lift schedule of the cam angle. This class is the
single source of truth for a cam: its ``displacement(theta)`` is the exact lift, and two consumers
read from it - the drawn cam BODY (``profile_points``) and the solver-facing prescribed MOTION
(``expression``). Because both derive from the same displacement, the drawn lobe and the follower
motion can never disagree.

Two authoring forms (professional cam-design idiom, cf. NX/Creo motion cam tracks):

- Legacy single law (sugar): ``{law = harmonic|sine, lift, lobes}`` - a smooth rise-fall repeated
  ``lobes`` times over the revolution (an eccentric/harmonic cam). harmonic and sine are identical
  (sin^2 == the raised cosine).
- Segmented (general): ``{segments = [ {kind = dwell, angle}, {kind = rise, law, angle, lift},
  {kind = return, law, angle[, fall]}, ... ]}`` - the classic dwell-rise-dwell-return schedule that
  reads as a real engine cam (a base-circle dwell + a distinct nose). Segment angles must sum to 360
  and the schedule must return to the base circle (a closed periodic profile). Rise/return laws:
  ``harmonic`` (raised cosine) or ``cycloidal`` (the low-vibration standard, C2 into a dwell).

``displacement`` is exact and piecewise. ``expression`` fits a truncated FOURIER SERIES (a sum of
sin/cos) to the displacement, because OndselSolver's motion grammar accepts smooth analytic terms
but REJECTS piecewise/conditional constructs; the max fit error is logged so the approximation is
honest. One class.
"""

import logging
import math

import numpy as np

logger = logging.getLogger(__name__)

_LEGACY_LAWS = frozenset({"harmonic", "sine"})
_RISE_LAWS = frozenset({"harmonic", "cycloidal"})
_FIT_HARMONICS = 24
_FIT_SAMPLES = 720
_COEFF_FLOOR_M = 1e-9  # drop Fourier terms below 1e-6 mm to keep the expression clean
_CLOSE_TOL = 1e-6


class CamProfileError(Exception):
    """A cam ``profile`` is malformed; reported by the builder as an id-attributed issue."""


class CamProfile:
    """A cam lift schedule (legacy single-law or segmented) with a base radius; one truth source."""

    def __init__(self, base_r: float, mode: str, legacy: dict | None,
                 segments: list[dict] | None) -> None:
        self._base_r = base_r
        self._mode = mode
        self._legacy = legacy or {}
        self._segments = segments or []

    @classmethod
    def from_profile(cls, profile: dict) -> "CamProfile":
        """Build from a cam coupling's ``profile`` dict; raise CamProfileError on bad params."""
        base_r = _positive(profile.get("base_r"), "base_r")
        if "segments" in profile:
            return cls(base_r, "segments", None, _build_segments(profile["segments"]))
        return cls(base_r, "legacy", _build_legacy(profile), None)

    def displacement(self, theta_deg: float) -> float:
        """The exact follower lift (mm) at cam angle ``theta_deg`` (0 <= lift <= the peak)."""
        if self._mode == "legacy":
            theta = math.radians(theta_deg)
            lobes = self._legacy["lobes"]
            return self._legacy["lift"] / 2.0 * (1.0 - math.cos(lobes * theta))
        return _segmented_displacement(self._segments, theta_deg % 360.0)

    def radius(self, theta_deg: float) -> float:
        """The polar cam-profile radius (mm) at ``theta_deg``: base circle + displacement."""
        return self._base_r + self.displacement(theta_deg)

    def profile_points(self, samples: int = 360) -> list[list[float]]:
        """The cam BODY outline as a closed [x, y] point list (mm), drawn to match the motion.

        A knife-edge follower sits at +Y (world 90 deg). When the cam is rotated by the driver angle
        theta, the profile point under the follower is at the cam's LOCAL angle 90 - theta, and its
        radius must equal base_r + displacement(theta) for the drawn lobe to raise the follower
        exactly as the schedule prescribes. So the local polar profile is
        r(phi) = base_r + displacement(90 - phi). Sampling phi over 0..360 gives the cam outline
        whose base circle + nose drive the follower in sync.
        """
        pts: list[list[float]] = []
        for i in range(samples):
            phi = 360.0 * i / samples
            r = self._base_r + self.displacement(90.0 - phi)
            a = math.radians(phi)
            pts.append([r * math.cos(a), r * math.sin(a)])
        return pts

    def expression(self, a0_deg: float, span_deg: float) -> str:
        """The follower's prescribed TRANSLATIONAL motion as a smooth function of ``time`` (metres).

        The driver sweeps the cam angle theta = a0 + span*time (deg) over t in [0, 1]. A truncated
        Fourier series (a sum of sin/cos, which the ASMT motion grammar accepts) is fitted to the
        exact displacement over one revolution, then re-expressed in ``time`` and scaled mm ->
        metres. The max fit error is logged.
        """
        thetas = np.arange(_FIT_SAMPLES) * (360.0 / _FIT_SAMPLES)
        disp_mm = np.array([self.displacement(float(t)) for t in thetas])
        spectrum = np.fft.rfft(disp_mm)
        max_k = min(_FIT_HARMONICS, len(spectrum) - 1)
        inner = f"({math.radians(a0_deg)} + {math.radians(span_deg)}*time)"
        pairs: list[tuple[float, str]] = [(float(spectrum[0].real) / _FIT_SAMPLES / 1000.0, "")]
        for k in range(1, max_k + 1):
            ak = 2.0 * float(spectrum[k].real) / _FIT_SAMPLES / 1000.0
            bk = -2.0 * float(spectrum[k].imag) / _FIT_SAMPLES / 1000.0
            if abs(ak) > _COEFF_FLOOR_M:
                pairs.append((ak, f"cos({k}*{inner})"))
            if abs(bk) > _COEFF_FLOOR_M:
                pairs.append((bk, f"sin({k}*{inner})"))
        self._log_fit_error(disp_mm, spectrum, max_k)
        return _assemble(pairs)

    def _log_fit_error(self, disp_mm: np.ndarray, spectrum: np.ndarray, max_k: int) -> None:
        """Reconstruct the truncated series on the fit grid and log the max error (mm)."""
        recon = np.full(_FIT_SAMPLES, float(spectrum[0].real) / _FIT_SAMPLES)
        theta = np.arange(_FIT_SAMPLES) * (2.0 * math.pi / _FIT_SAMPLES)
        for k in range(1, max_k + 1):
            recon += (2.0 * float(spectrum[k].real) / _FIT_SAMPLES) * np.cos(k * theta)
            recon += (-2.0 * float(spectrum[k].imag) / _FIT_SAMPLES) * np.sin(k * theta)
        err = float(np.max(np.abs(recon - disp_mm)))
        logger.info("cam Fourier fit: %d harmonics, max error %.3f mm", max_k, err)


def _build_legacy(profile: dict) -> dict:
    """Validate and normalize the legacy single-law form into {lift, lobes}."""
    raw_law = profile.get("law")
    if not isinstance(raw_law, str) or raw_law not in _LEGACY_LAWS:
        raise CamProfileError(f"cam law {raw_law!r} unknown; expected {sorted(_LEGACY_LAWS)}")
    lift = _positive(profile.get("lift"), "lift")
    lobes = profile.get("lobes", 1)
    if not isinstance(lobes, int) or lobes < 1:
        raise CamProfileError("cam 'lobes' must be a positive integer")
    return {"lift": lift, "lobes": lobes}


def _build_segments(raw: list) -> list[dict]:
    """Lower authored segments into cumulative {kind, law, start, span, start_level, delta} records.

    Tracks the running lift level so each segment carries its start level and signed delta;
    validates that the segment angles sum to 360, the level never dips below the base circle, and
    the schedule closes back to the base circle (a periodic cam profile).
    """
    if not isinstance(raw, list) or not raw:
        raise CamProfileError("cam 'segments' must be a non-empty list")
    segments: list[dict] = []
    cursor = 0.0
    level = 0.0
    for seg in raw:
        kind = seg.get("kind")
        span = _positive(seg.get("angle"), "angle")
        if kind == "dwell":
            segments.append(_segment("dwell", None, cursor, span, level, 0.0))
        elif kind == "rise":
            law = _rise_law(seg)
            delta = _positive(seg.get("lift"), "lift")
            segments.append(_segment("rise", law, cursor, span, level, delta))
            level += delta
        elif kind == "return":
            law = _rise_law(seg)
            fall = _positive(seg.get("fall", level), "fall")
            if fall > level + _CLOSE_TOL:
                raise CamProfileError("cam 'return' falls below the base circle")
            segments.append(_segment("return", law, cursor, span, level, -fall))
            level -= fall
        else:
            raise CamProfileError(f"cam segment kind {kind!r} unknown (dwell/rise/return)")
        cursor += span
    if not math.isclose(cursor, 360.0, abs_tol=1e-6):
        raise CamProfileError(f"cam segment angles must sum to 360 (got {cursor})")
    if not math.isclose(level, 0.0, abs_tol=1e-6):
        raise CamProfileError("cam segments must return to the base circle (net lift 0)")
    return segments


def _segment(kind: str, law: str | None, start: float, span: float,
             start_level: float, delta: float) -> dict:
    """A normalized segment record."""
    return {"kind": kind, "law": law, "start": start, "span": span,
            "start_level": start_level, "delta": delta}


def _rise_law(seg: dict) -> str:
    """The rise/return law for a segment (default cycloidal); raise on an unknown law."""
    law = seg.get("law", "cycloidal")
    if law not in _RISE_LAWS:
        raise CamProfileError(f"cam rise/return law {law!r} unknown; expected {sorted(_RISE_LAWS)}")
    return law


def _segmented_displacement(segments: list[dict], theta_deg: float) -> float:
    """Evaluate the piecewise displacement (mm) at ``theta_deg`` in [0, 360)."""
    for seg in segments:
        if seg["start"] <= theta_deg < seg["start"] + seg["span"] + _CLOSE_TOL:
            if seg["kind"] == "dwell":
                return seg["start_level"]
            u = (theta_deg - seg["start"]) / seg["span"]
            return seg["start_level"] + seg["delta"] * _normalized(seg["law"], u)
    return segments[-1]["start_level"] + segments[-1]["delta"]


def _normalized(law: str, u: float) -> float:
    """The normalized rise fraction (0 at u=0, 1 at u=1, 0.5 at u=0.5) for a rise/return law."""
    u = min(max(u, 0.0), 1.0)
    if law == "harmonic":
        return 0.5 * (1.0 - math.cos(math.pi * u))
    # cycloidal: u - sin(2*pi*u)/(2*pi) - zero velocity + acceleration at both ends.
    return u - math.sin(2.0 * math.pi * u) / (2.0 * math.pi)


def _assemble(pairs: list[tuple[float, str]]) -> str:
    """Assemble (coefficient, basis) pairs into a signed math expression (no '+ -')."""
    out = ""
    for i, (coeff, basis) in enumerate(pairs):
        token = f"{abs(coeff)}" if not basis else f"{abs(coeff)}*{basis}"
        if i == 0:
            out = ("-" + token) if coeff < 0 else token
        else:
            out += (" - " if coeff < 0 else " + ") + token
    return out or "0.0"


def _positive(value, name: str) -> float:
    """Return ``value`` as a positive float, or raise CamProfileError."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise CamProfileError(f"cam '{name}' must be a positive number")
    return float(value)
