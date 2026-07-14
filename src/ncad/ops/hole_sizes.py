"""Hole sizing: a named size + fit resolves to a drill diameter; a size resolves to a pitch.

Metric clearance-hole diameters follow ISO 273 (close / medium=normal / coarse=loose fit);
metric tapped diameters follow standard coarse-thread tap charts (major minus pitch).
Imperial sizes (UNC number + fractional) resolve to inch-based clearance drills converted to
mm. Coarse-thread pitches (metric + UNC) drive modeled threads. A bounded but professional
table; finer fit classes (H7/g6-style) remain a later refinement.
"""

_MM_PER_IN = 25.4

# size -> {"close", "normal", "loose", "tapped"} drill diameters in mm.
# metric clearance: ISO 273; tapped: metric coarse-thread tap-drill (major minus pitch).
# imperial: UNC number/fractional clearance drills (inch), stored in mm.
_TABLE: dict[str, dict[str, float]] = {
    "M2": {"close": 2.2, "normal": 2.4, "loose": 2.6, "tapped": 1.6},
    "M2.5": {"close": 2.7, "normal": 2.9, "loose": 3.1, "tapped": 2.05},
    "M3": {"close": 3.2, "normal": 3.4, "loose": 3.6, "tapped": 2.5},
    "M4": {"close": 4.3, "normal": 4.5, "loose": 4.8, "tapped": 3.3},
    "M5": {"close": 5.3, "normal": 5.5, "loose": 5.8, "tapped": 4.2},
    "M6": {"close": 6.4, "normal": 6.6, "loose": 7.0, "tapped": 5.0},
    "M8": {"close": 8.4, "normal": 9.0, "loose": 10.0, "tapped": 6.8},
    "M10": {"close": 10.5, "normal": 11.0, "loose": 12.0, "tapped": 8.5},
    "M12": {"close": 13.0, "normal": 13.5, "loose": 14.5, "tapped": 10.2},
    "M16": {"close": 17.0, "normal": 17.5, "loose": 18.5, "tapped": 14.0},
    "M20": {"close": 21.0, "normal": 22.0, "loose": 24.0, "tapped": 17.5},
    # Imperial UNC number sizes; clearance drills in mm.
    "#4": {"close": 2.85, "normal": 3.10, "loose": 3.30, "tapped": 2.26},
    "#6": {"close": 3.51, "normal": 3.73, "loose": 4.04, "tapped": 2.85},
    "#8": {"close": 4.17, "normal": 4.50, "loose": 4.76, "tapped": 3.44},
    "#10": {"close": 4.90, "normal": 5.11, "loose": 5.49, "tapped": 3.86},
    # Imperial fractional sizes.
    "1/4": {"close": 6.75, "normal": 7.14, "loose": 7.54, "tapped": 5.11},
    "5/16": {"close": 8.33, "normal": 8.73, "loose": 9.13, "tapped": 6.53},
    "3/8": {"close": 9.93, "normal": 10.32, "loose": 10.72, "tapped": 8.03},
    "1/2": {"close": 13.10, "normal": 13.49, "loose": 14.29, "tapped": 10.80},
}

# Coarse-thread pitch (mm) per size, for modeled threads. Metric coarse (ISO 261); imperial
# UNC threads-per-inch converted to a mm pitch (25.4 / TPI).
_PITCH: dict[str, float] = {
    "M2": 0.4, "M2.5": 0.45, "M3": 0.5, "M4": 0.7, "M5": 0.8, "M6": 1.0,
    "M8": 1.25, "M10": 1.5, "M12": 1.75, "M16": 2.0, "M20": 2.5,
    "#4": _MM_PER_IN / 40, "#6": _MM_PER_IN / 32, "#8": _MM_PER_IN / 32,
    "#10": _MM_PER_IN / 24, "1/4": _MM_PER_IN / 20, "5/16": _MM_PER_IN / 18,
    "3/8": _MM_PER_IN / 16, "1/2": _MM_PER_IN / 13,
}

# Major (nominal) diameter (mm) per size, for a modeled thread's crest diameter.
_MAJOR: dict[str, float] = {
    "M2": 2.0, "M2.5": 2.5, "M3": 3.0, "M4": 4.0, "M5": 5.0, "M6": 6.0,
    "M8": 8.0, "M10": 10.0, "M12": 12.0, "M16": 16.0, "M20": 20.0,
    "#4": 0.112 * _MM_PER_IN, "#6": 0.138 * _MM_PER_IN, "#8": 0.164 * _MM_PER_IN,
    "#10": 0.190 * _MM_PER_IN, "1/4": 0.25 * _MM_PER_IN, "5/16": 0.3125 * _MM_PER_IN,
    "3/8": 0.375 * _MM_PER_IN, "1/2": 0.5 * _MM_PER_IN,
}


class HoleSizeTable:
    """Resolves a named hole size + fit to a drill diameter, and to thread pitch/major (mm)."""

    def resolve_diameter(self, size: str, fit: str) -> float:
        """The drill diameter (mm) for ``size`` (e.g. ``"M6"``, ``"#10"``, ``"1/4"``) at ``fit``.

        :raises ValueError: If ``size`` or ``fit`` is not in the table.
        """
        if size not in _TABLE:
            raise ValueError(
                f"unknown hole size {size!r}; expected one of {sorted(_TABLE)}")
        fits = _TABLE[size]
        if fit not in fits:
            raise ValueError(f"unknown hole fit {fit!r}; expected one of {sorted(fits)}")
        return fits[fit]

    def pitch(self, size: str) -> float:
        """The coarse-thread pitch (mm) for ``size`` (for a modeled thread)."""
        if size not in _PITCH:
            raise ValueError(
                f"no thread pitch for size {size!r}; expected one of {sorted(_PITCH)}")
        return _PITCH[size]

    def major_diameter(self, size: str) -> float:
        """The nominal (major) diameter (mm) for ``size`` (a modeled thread's crest)."""
        if size not in _MAJOR:
            raise ValueError(
                f"no major diameter for size {size!r}; expected one of {sorted(_MAJOR)}")
        return _MAJOR[size]
