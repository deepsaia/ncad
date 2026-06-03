"""Geometric validation: openings fit their walls and do not overlap.

Cheap, deterministic checks over the spec — most "broken building" cases are catchable
here without any geometry kernel or vision model (design.md §5).
"""

import logging
import math

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)

_EPSILON = 1e-9


class GeometryValidator:
    """Validates that openings fit within their walls and don't overlap each other."""

    def validate(self, spec: dict) -> list[Issue]:
        """Return geometric issues for ``spec`` (empty if none)."""
        issues: list[Issue] = []
        for storey in spec["storeys"]:
            storey_height = storey["height"]
            for wall in storey["walls"]:
                issues.extend(self._validate_wall(wall, storey_height))
        return issues

    def _validate_wall(self, wall: dict, storey_height: float) -> list[Issue]:
        issues: list[Issue] = []
        length = _wall_length(wall)
        height = wall.get("height") or storey_height
        spans = []
        for opening in wall.get("openings", []):
            issues.extend(self._validate_opening_fit(opening, wall["id"], length, height))
            spans.append((opening["id"], *self._opening_span(opening, length)))
        issues.extend(self._validate_no_overlap(spans))
        return issues

    def _validate_opening_fit(
        self, opening: dict, wall_id: str, length: float, height: float
    ) -> list[Issue]:
        issues: list[Issue] = []
        low, high = self._opening_span(opening, length)
        if low < -_EPSILON or high > length + _EPSILON:
            issues.append(
                Issue(
                    kind="opening_out_of_bounds",
                    entity_id=opening["id"],
                    message=(
                        f"opening {opening['id']!r} spans [{low:.2f}, {high:.2f}] m "
                        f"outside wall {wall_id!r} length {length:.2f} m"
                    ),
                )
            )
        top = opening.get("sill", 0.0) + opening["height"]
        if top > height + _EPSILON:
            issues.append(
                Issue(
                    kind="opening_too_tall",
                    entity_id=opening["id"],
                    message=(
                        f"opening {opening['id']!r} top {top:.2f} m exceeds wall height "
                        f"{height:.2f} m"
                    ),
                )
            )
        return issues

    def _validate_no_overlap(self, spans: list[tuple]) -> list[Issue]:
        issues: list[Issue] = []
        ordered = sorted(spans, key=lambda s: s[1])
        for earlier, later in zip(ordered, ordered[1:]):
            if later[1] < earlier[2] - _EPSILON:
                issues.append(
                    Issue(
                        kind="opening_overlap",
                        entity_id=later[0],
                        message=f"openings {earlier[0]!r} and {later[0]!r} overlap on their wall",
                    )
                )
        return issues

    def _opening_span(self, opening: dict, length: float) -> tuple[float, float]:
        center = opening["along"] * length
        half = opening["width"] / 2.0
        return center - half, center + half


def _wall_length(wall: dict) -> float:
    if "arc" in wall:
        cx, cy = wall["arc"]["center"]
        (sx, sy), (ex, ey) = wall["start"], wall["end"]
        radius = math.hypot(sx - cx, sy - cy)
        sweep = abs(math.atan2(ey - cy, ex - cx) - math.atan2(sy - cy, sx - cx))
        if sweep > math.pi:
            sweep = 2 * math.pi - sweep
        return radius * sweep
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return math.hypot(x1 - x0, y1 - y0)
