"""Resolve an airfoil sketch entity to section points: NACA 4-digit generation or a .dat file.

Dispatches the two authoring forms to a single closed point loop scaled to the chord, ready to
lower into an interpolated spline. NACA uses the pure NacaAirfoil generator; ``dat`` parses a
Selig/Lednicer coordinate file (path resolved via SpecReference relative to the doc). Contract
violations raise AirfoilParamError (EntityExpander wraps it into a BuildIssue). One class.
"""

import logging

from ncad.sketch.naca_airfoil import NacaAirfoil
from ncad.spec.spec_reference import SpecReference

logger = logging.getLogger(__name__)

_MIN_POINTS = 3


class AirfoilParamError(Exception):
    """An airfoil entity has no/both source(s), a bad chord/code, or an unreadable .dat file."""


class AirfoilProfile:
    """Resolves an airfoil entity (naca | dat) to a closed, chord-scaled section point loop."""

    def points(self, params: dict, base_dir: str | None = None) -> list[list[float]]:
        """Return the section as ``[[x, y], ...]`` scaled to ``chord``, a closed loop."""
        naca = params.get("naca")
        dat = params.get("dat")
        if bool(naca) == bool(dat):
            raise AirfoilParamError("airfoil needs exactly one of 'naca' or 'dat'")
        chord = float(params.get("chord", 0.0))
        if chord <= 0.0:
            raise AirfoilParamError(f"airfoil 'chord' must be > 0; got {chord}")
        unit = (self._naca_points(str(naca), params) if naca
                else self._dat_points(str(dat), base_dir))
        if len(unit) < _MIN_POINTS:
            raise AirfoilParamError(f"airfoil section has too few points ({len(unit)})")
        loop = [[round(x * chord, 6), round(y * chord, 6)] for x, y in unit]
        if loop[0] != loop[-1]:
            loop.append(list(loop[0]))   # close the loop for a valid face
        return loop

    def _naca_points(self, code: str, params: dict) -> list[tuple[float, float]]:
        """Generate NACA 4-digit section points; convert a bad code to AirfoilParamError."""
        try:
            return NacaAirfoil(str(code)).points(int(params.get("samples", 60)))
        except ValueError as exc:
            raise AirfoilParamError(str(exc)) from exc

    def _dat_points(self, dat: str, base_dir: str | None) -> list[tuple[float, float]]:
        """Parse a Selig/Lednicer .dat file into unit-chord (x, y) pairs."""
        if base_dir is None:
            raise AirfoilParamError(
                f"airfoil 'dat' {dat!r} needs a document directory to resolve")
        path = SpecReference().resolve(str(dat), base_dir)
        try:
            with open(path, encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError as exc:
            raise AirfoilParamError(f"airfoil 'dat' {dat!r} could not be read: {exc}") from exc
        return _parse_dat(lines)


def _parse_dat(lines: list[str]) -> list[tuple[float, float]]:
    """Extract (x, y) coordinate pairs from a .dat file, skipping header/blank/count lines."""
    pts: list[tuple[float, float]] = []
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            continue   # a name header line
        # A Lednicer file carries a leading "count count" line with values > 1; skip non-unit-chord
        # coordinates so both orderings feed the same unit-chord loop.
        if abs(x) > 1.5 or abs(y) > 1.5:
            continue
        pts.append((x, y))
    return pts
