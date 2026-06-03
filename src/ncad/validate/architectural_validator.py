"""Architectural-sanity validation: minimum room area, ceiling height, door width.

Encodes a few habitability minimums so generated or edited specs don't drift into
nonsense (closet-sized rooms, crawl-space ceilings). Thresholds are configurable.
"""

import logging

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)


class ArchitecturalValidator:
    """Validates basic architectural minimums."""

    def __init__(
        self,
        min_room_area: float = 4.0,
        min_ceiling_height: float = 2.2,
        min_door_width: float = 0.7,
    ) -> None:
        """:param min_room_area: Minimum room floor area, m^2.
        :param min_ceiling_height: Minimum floor-to-floor height, m.
        :param min_door_width: Minimum door leaf width, m.
        """
        self._min_room_area = min_room_area
        self._min_ceiling_height = min_ceiling_height
        self._min_door_width = min_door_width

    def validate(self, spec: dict) -> list[Issue]:
        """Return architectural issues for ``spec`` (empty if all minimums met)."""
        issues: list[Issue] = []
        for index, storey in enumerate(spec["storeys"]):
            if storey["height"] < self._min_ceiling_height:
                issues.append(
                    Issue(
                        kind="min_ceiling_height",
                        entity_id="<storey>",
                        message=(
                            f"ceiling height {storey['height']:.2f} m below minimum "
                            f"{self._min_ceiling_height:.2f} m"
                        ),
                    )
                )
            # Balconies belong on upper storeys only — never the ground floor.
            if index == 0 and storey.get("balconies"):
                issues.append(
                    Issue(
                        kind="balcony_on_ground_floor",
                        entity_id="<storey>",
                        message="balconies are not allowed on the ground floor (storey 0)",
                    )
                )
            issues.extend(self._validate_rooms(storey["rooms"]))
            issues.extend(self._validate_doors(storey["walls"]))
        return issues

    def _validate_rooms(self, rooms: list[dict]) -> list[Issue]:
        issues: list[Issue] = []
        for room in rooms:
            area = _polygon_area(room["polygon"])
            if area < self._min_room_area:
                issues.append(
                    Issue(
                        kind="min_room_area",
                        entity_id=room["id"],
                        message=(
                            f"room {room['id']!r} area {area:.2f} m^2 below minimum "
                            f"{self._min_room_area:.2f} m^2"
                        ),
                    )
                )
        return issues

    def _validate_doors(self, walls: list[dict]) -> list[Issue]:
        issues: list[Issue] = []
        for wall in walls:
            for opening in wall.get("openings", []):
                if opening["kind"] == "door" and opening["width"] < self._min_door_width:
                    issues.append(
                        Issue(
                            kind="min_door_width",
                            entity_id=opening["id"],
                            message=(
                                f"door {opening['id']!r} width {opening['width']:.2f} m below "
                                f"minimum {self._min_door_width:.2f} m"
                            ),
                        )
                    )
        return issues


def _polygon_area(polygon: list) -> float:
    area = 0.0
    count = len(polygon)
    for i in range(count):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % count]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0
