"""Compute a bill of materials by traversing the spec.

Quantities come from parametric values — ``length x thickness x height`` minus opening
volumes, polygon areas via the shoelace formula — never measured from the built mesh
(design.md §4). This keeps the BOM exact, deterministic, and a cheap regression check.
"""

import logging
import math

from ncad.bom.bom import Bom

logger = logging.getLogger(__name__)


class BomCalculator:
    """Folds a spec into aggregate quantities."""

    def quantities(self, spec: dict) -> Bom:
        """Compute the BOM for ``spec``.

        :param spec: A schema-valid building spec dict.
        :return: A :class:`Bom` of aggregate quantities.
        """
        wall_volume = 0.0
        wall_face_area = 0.0
        door_count = 0
        window_count = 0
        floor_area = 0.0

        for storey in spec["storeys"]:
            storey_height = storey["height"]
            for wall in storey["walls"]:
                length = _wall_length(wall)
                height = wall.get("height") or storey_height
                thickness = wall["thickness"]
                gross_face = length * height
                opening_face = _opening_face_area(wall)
                wall_face_area += gross_face - opening_face
                wall_volume += (gross_face - opening_face) * thickness
                doors, windows = _count_openings(wall)
                door_count += doors
                window_count += windows
            floor_area += sum(_polygon_area(room["polygon"]) for room in storey["rooms"])

        # Roof covers the footprint, which is the union of rooms (robust to non-
        # rectangular footprints later). For v1 single-storey, that equals floor_area.
        roof_area = floor_area
        bom = Bom(
            wall_volume=wall_volume,
            wall_face_area=wall_face_area,
            door_count=door_count,
            window_count=window_count,
            floor_area=floor_area,
            roof_area=roof_area,
        )
        logger.debug("computed BOM: %s", bom.as_dict())
        return bom


def _wall_length(wall: dict) -> float:
    if "arc" in wall:
        return _arc_length(wall)
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return math.hypot(x1 - x0, y1 - y0)


def _arc_length(wall: dict) -> float:
    """Length of a curved wall: radius times the included angle."""
    cx, cy = wall["arc"]["center"]
    (sx, sy), (ex, ey) = wall["start"], wall["end"]
    radius = math.hypot(sx - cx, sy - cy)
    sweep = abs(math.atan2(ey - cy, ex - cx) - math.atan2(sy - cy, sx - cx))
    if sweep > math.pi:
        sweep = 2 * math.pi - sweep
    return radius * sweep


def _opening_face_area(wall: dict) -> float:
    return sum(o["width"] * o["height"] for o in wall.get("openings", []))


def _count_openings(wall: dict) -> tuple[int, int]:
    doors = sum(1 for o in wall.get("openings", []) if o["kind"] == "door")
    windows = sum(1 for o in wall.get("openings", []) if o["kind"] == "window")
    return doors, windows


def _polygon_area(polygon: list) -> float:
    """Shoelace area of a (non-closed) polygon."""
    area = 0.0
    count = len(polygon)
    for i in range(count):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % count]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0
