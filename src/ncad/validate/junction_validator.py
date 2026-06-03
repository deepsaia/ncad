"""Validation that openings do not sit on or near a wall junction.

A door or window whose span reaches a wall's *joined* endpoint (a corner shared with
another wall) reads as broken: the opening collides with whatever is on the adjoining
wall across the corner (e.g. a door that looks split by a window on the perpendicular
wall). Openings must stay clear of junctions by a minimum clearance.

Angle-agnostic: it works from endpoint coincidence and along-the-wall spans, so it
applies to axis-aligned, diagonal, and (in principle) arc-adjacent walls alike.
"""

import logging
import math
from collections import Counter

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)

_TOLERANCE = 4  # decimals for snapping endpoints
_MIN_JUNCTION_CLEARANCE = 0.3  # meters an opening must stay clear of a junction


class JunctionValidator:
    """Flags openings whose span comes too close to a wall's joined endpoint."""

    def validate(self, spec: dict) -> list[Issue]:
        """Return junction issues for ``spec`` (empty if all openings clear junctions)."""
        issues: list[Issue] = []
        for storey in spec["storeys"]:
            issues.extend(self._validate_storey(storey))
        return issues

    def _validate_storey(self, storey: dict) -> list[Issue]:
        junctions = self._junction_points(storey["walls"])
        issues: list[Issue] = []
        for wall in storey["walls"]:
            issues.extend(self._validate_wall(wall, junctions))
        return issues

    def _junction_points(self, walls: list[dict]) -> set:
        """Endpoint coordinates shared by more than one wall (i.e. wall corners)."""
        degree: Counter = Counter()
        for wall in walls:
            for point in (wall["start"], wall["end"]):
                degree[(round(point[0], _TOLERANCE), round(point[1], _TOLERANCE))] += 1
        return {point for point, count in degree.items() if count > 1}

    def _validate_wall(self, wall: dict, junctions: set) -> list[Issue]:
        length = _wall_length(wall)
        if length == 0:
            return []
        # Distance from the wall's start/end to a junction (0 if that end is a junction).
        start_is_junction = _snap(wall["start"]) in junctions
        end_is_junction = _snap(wall["end"]) in junctions

        issues: list[Issue] = []
        for opening in wall.get("openings", []):
            center = opening["along"] * length
            half = opening["width"] / 2.0
            near = center - half  # distance from start end
            far = length - (center + half)  # distance from end
            if start_is_junction and near < _MIN_JUNCTION_CLEARANCE:
                issues.append(_issue(opening, wall, near))
            elif end_is_junction and far < _MIN_JUNCTION_CLEARANCE:
                issues.append(_issue(opening, wall, far))
        return issues


def _issue(opening: dict, wall: dict, gap: float) -> Issue:
    return Issue(
        kind="opening_near_junction",
        entity_id=opening["id"],
        message=(
            f"opening {opening['id']!r} on wall {wall['id']!r} is {gap:.2f} m from a wall "
            f"junction (min clearance {_MIN_JUNCTION_CLEARANCE} m); it would collide with "
            "openings on the joined wall"
        ),
    )


def _wall_length(wall: dict) -> float:
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return math.hypot(x1 - x0, y1 - y0)


def _snap(point) -> tuple:
    return (round(point[0], _TOLERANCE), round(point[1], _TOLERANCE))
