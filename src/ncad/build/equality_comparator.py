"""Compare two geometry signatures under the section-4a equality definition.

Topology (element counts and surface/curve-type histograms) must match exactly;
measures (volume, area, bounding box, centre of gravity) must agree within a
relative + absolute tolerance. This is what golden tests assert and what a cache hit
must reproduce. A raw BREP-byte hash is deliberately not the equality test.
"""

import logging
import math

logger = logging.getLogger(__name__)

_TOPOLOGY_FIELDS = ("counts", "surface_types", "curve_types")
_SCALAR_MEASURES = ("volume", "area")
_TUPLE_MEASURES = ("bbox", "cog")


class EqualityComparator:
    """Decides whether two signatures are equal under tolerance."""

    def __init__(self, rtol: float = 1e-6, atol: float = 1e-9) -> None:
        self._rtol = rtol
        self._atol = atol

    def equal(self, a: dict, b: dict) -> bool:
        """True when topology matches exactly and measures agree within tolerance."""
        return not self.explain(a, b)

    def explain(self, a: dict, b: dict) -> list[str]:
        """Names of the fields that differ; empty when equal."""
        mismatches: list[str] = []
        for field in _TOPOLOGY_FIELDS:
            if a.get(field) != b.get(field):
                mismatches.append(field)
        for field in _SCALAR_MEASURES:
            if not self._close(a.get(field), b.get(field)):
                mismatches.append(field)
        for field in _TUPLE_MEASURES:
            if not self._close_nested(a.get(field), b.get(field)):
                mismatches.append(field)
        return mismatches

    def _close(self, x, y) -> bool:
        """Scalar closeness under the configured tolerances."""
        if x is None or y is None:
            return x == y
        return math.isclose(x, y, rel_tol=self._rtol, abs_tol=self._atol)

    def _close_nested(self, x, y) -> bool:
        """Element-wise closeness for a flat or nested numeric tuple."""
        if x is None or y is None:
            return x == y
        if isinstance(x, (tuple, list)) and isinstance(y, (tuple, list)):
            return len(x) == len(y) and all(self._close_nested(u, v) for u, v in zip(x, y))
        return self._close(x, y)
