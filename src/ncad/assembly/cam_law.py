"""A smooth closed-form cam law: the follower lift as a function of cam angle.

A cam coupling drives a translating follower by a lift law of the cam angle. OndselSolver's motion
expression grammar accepts smooth analytic functions (sin/cos/products/polynomials) but REJECTS
piecewise/conditional constructs, so ncad uses smooth full-cycle laws (a rise-fall per lobe), not a
piecewise rise-dwell-fall or a sampled table. This is an eccentric / harmonic cam - a classic,
recognizable cam.

Laws (theta in radians, over one revolution; ``lobes`` lifts per revolution):
- harmonic: lift/2 * (1 - cos(lobes * theta))       - smooth cosine rise-fall, peak `lift`.
- sine:     lift * sin(lobes * theta / 2)^2         - equivalent smooth rise-fall (== harmonic).

Provides ``lift(theta_deg)`` (mm), ``radius(theta_deg)`` = base_r + lift (the polar cam profile,
mm), and ``expression(a0_deg, span_deg)`` = the follower's prescribed TRANSLATIONAL motion as a
smooth function of ``time`` in METRES (the driver sweeps a0..a0+span deg over t 0..1). One class.
"""

import math

_LAWS = frozenset({"harmonic", "sine"})


class CamLawError(Exception):
    """A cam ``profile`` is malformed; reported by the builder as an id-attributed issue."""


class CamLaw:
    """A smooth cam lift law (harmonic / sine) with a base radius, lift, and lobe count."""

    def __init__(self, law: str, base_r: float, lift: float, lobes: int) -> None:
        self._law = law
        self._base_r = base_r
        self._lift = lift
        self._lobes = lobes

    @classmethod
    def from_profile(cls, profile: dict) -> "CamLaw":
        """Build from a cam coupling's ``profile`` dict; raise CamLawError on bad law/params."""
        raw_law = profile.get("law")
        if not isinstance(raw_law, str) or raw_law not in _LAWS:
            raise CamLawError(f"cam law {raw_law!r} unknown; expected one of {sorted(_LAWS)}")
        law: str = raw_law
        base_r = _positive(profile.get("base_r"), "base_r")
        lift = _positive(profile.get("lift"), "lift")
        lobes = profile.get("lobes", 1)
        if not isinstance(lobes, int) or lobes < 1:
            raise CamLawError("cam 'lobes' must be a positive integer")
        return cls(law, base_r, lift, lobes)

    def lift(self, theta_deg: float) -> float:
        """The follower lift (mm) at cam angle ``theta_deg`` (0 <= lift <= the declared lift)."""
        theta = math.radians(theta_deg)
        if self._law == "harmonic":
            return self._lift / 2.0 * (1.0 - math.cos(self._lobes * theta))
        s = math.sin(self._lobes * theta / 2.0)
        return self._lift * s * s

    def radius(self, theta_deg: float) -> float:
        """The polar cam-profile radius (mm) at ``theta_deg``: base circle + lift."""
        return self._base_r + self.lift(theta_deg)

    def expression(self, a0_deg: float, span_deg: float) -> str:
        """The follower's prescribed TRANSLATIONAL motion as a smooth function of ``time`` (metres).

        The driver sweeps the cam angle theta = a0 + span*time (deg) over t in [0, 1]; substituted
        into the lift law (in radians) and scaled mm -> metres for the ASMT translational motion.
        """
        # theta in radians as a function of time: (a0 + span*time) * pi/180.
        a0_rad = math.radians(a0_deg)
        span_rad = math.radians(span_deg)
        # inner = lobes * theta(time)
        inner = f"{self._lobes} * ({a0_rad} + {span_rad}*time)"
        lift_m = self._lift / 1000.0
        if self._law == "harmonic":
            return f"{lift_m / 2.0} * (1 - cos({inner}))"
        # sine: lift * sin(inner/2)^2
        return f"{lift_m} * sin(({inner})/2) * sin(({inner})/2)"


def _positive(value, name: str) -> float:
    """Return ``value`` as a positive float, or raise CamLawError."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise CamLawError(f"cam '{name}' must be a positive number")
    return float(value)
