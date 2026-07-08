"""ISO-metric hole sizing: a named size + fit resolves to a drill diameter.

Clearance-hole diameters follow ISO 273 (close / medium=normal / coarse=loose fit);
tap-drill diameters follow standard metric coarse-thread tap charts. A small, bounded
table (M3-M10); ANSI/imperial and finer fit classes are deferred (see the plan backlog).
"""

# size -> {"close", "normal", "loose", "tapped"} drill diameters in mm.
# clearance: ISO 273. tapped: metric coarse-thread tap-drill (major minus pitch).
_TABLE: dict[str, dict[str, float]] = {
    "M3": {"close": 3.2, "normal": 3.4, "loose": 3.6, "tapped": 2.5},
    "M4": {"close": 4.3, "normal": 4.5, "loose": 4.8, "tapped": 3.3},
    "M5": {"close": 5.3, "normal": 5.5, "loose": 5.8, "tapped": 4.2},
    "M6": {"close": 6.4, "normal": 6.6, "loose": 7.0, "tapped": 5.0},
    "M8": {"close": 8.4, "normal": 9.0, "loose": 10.0, "tapped": 6.8},
    "M10": {"close": 10.5, "normal": 11.0, "loose": 12.0, "tapped": 8.5},
}


class HoleSizeTable:
    """Resolves an ISO-metric hole size + fit to a drill diameter (mm)."""

    def resolve_diameter(self, size: str, fit: str) -> float:
        """The drill diameter for ``size`` (e.g. ``"M6"``) at ``fit``.

        :raises ValueError: If ``size`` or ``fit`` is not in the table.
        """
        if size not in _TABLE:
            raise ValueError(
                f"unknown hole size {size!r}; expected one of {sorted(_TABLE)}")
        fits = _TABLE[size]
        if fit not in fits:
            raise ValueError(f"unknown hole fit {fit!r}; expected one of {sorted(fits)}")
        return fits[fit]
