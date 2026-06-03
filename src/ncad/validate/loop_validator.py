"""Topological validation that the exterior walls form a closed loop.

Angle-agnostic: it compares only endpoint *coordinates*, so axis-aligned, diagonal, and
arc walls all participate identically. In a closed perimeter every exterior wall endpoint
coincides with an even number of other exterior wall ends (each junction is shared); an
odd-degree endpoint is a dangling end — a gap in the building's outline.

Interior partition walls (id prefixed ``interior_``) legitimately terminate against the
perimeter mid-span (T-junctions), so they are excluded from the loop check.
"""

import logging
from collections import Counter

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)

_TOLERANCE = 4  # decimal places for snapping endpoints together
_INTERIOR_PREFIX = "interior_"


class LoopValidator:
    """Validates that each storey's exterior walls close into a loop."""

    def validate(self, spec: dict) -> list[Issue]:
        """Return loop issues for ``spec`` (empty if every exterior loop is closed)."""
        issues: list[Issue] = []
        for storey in spec["storeys"]:
            issues.extend(self._validate_storey(storey))
        return issues

    def _validate_storey(self, storey: dict) -> list[Issue]:
        degree: Counter = Counter()
        for wall in storey["walls"]:
            if wall["id"].startswith(_INTERIOR_PREFIX):
                continue
            for point in (wall["start"], wall["end"]):
                degree[(round(point[0], _TOLERANCE), round(point[1], _TOLERANCE))] += 1

        dangling = [point for point, count in degree.items() if count % 2 != 0]
        if not dangling:
            return []
        return [
            Issue(
                kind="open_wall_loop",
                entity_id="<storey>",
                message=(
                    "exterior walls do not form a closed loop; dangling endpoint(s) at "
                    f"{sorted(dangling)}"
                ),
            )
        ]
