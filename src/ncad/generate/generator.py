"""Generate a building spec from a seed and parameters.

This is the one place randomness lives: ``generate`` seeds a single ``random.Random``
from ``seed`` and threads it into the subdivider. Same ``(seed, params)`` therefore
yields an identical spec (golden-spec determinism, design.md §0). The output is a plain
dict conforming to ``schema/building_schema.hocon``.
"""

import logging
import math
import random

from ncad.generate.bsp_subdivider import BspSubdivider
from ncad.generate.footprint_grid import FootprintGrid
from ncad.generate.opening_placer import OpeningPlacer
from ncad.generate.rectangle import Rectangle
from ncad.generate.subdivision import Subdivision

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = 1
_DEFAULT_WIDTH = 12.0
_DEFAULT_DEPTH = 9.0
_DEFAULT_NUM_ROOMS = 4
_DEFAULT_STOREY_HEIGHT = 3.0
_DEFAULT_WALL_THICKNESS = 0.2
_DEFAULT_MIN_ROOM_SIZE = 2.0
_DEFAULT_ROOF_THICKNESS = 0.2
_RECT_SHAPE = "rect"


class Generator:
    """Turns parameters + a seed into a schema-valid building spec dict."""

    def __init__(self, params: dict) -> None:
        """:param params: Generation parameters. Recognized keys: ``width``, ``depth``,
        ``num_rooms``, ``storey_height``, ``wall_thickness``, ``min_room_size``.
        """
        self._width = params.get("width", _DEFAULT_WIDTH)
        self._depth = params.get("depth", _DEFAULT_DEPTH)
        self._num_rooms = params.get("num_rooms", _DEFAULT_NUM_ROOMS)
        self._storey_height = params.get("storey_height", _DEFAULT_STOREY_HEIGHT)
        self._wall_thickness = params.get("wall_thickness", _DEFAULT_WALL_THICKNESS)
        self._min_room_size = params.get("min_room_size", _DEFAULT_MIN_ROOM_SIZE)
        self._footprint_shape = params.get("footprint_shape", _RECT_SHAPE)
        self._roof_kind = params.get("roof_kind", "flat")

    def generate(self, seed: int) -> dict:
        """Generate the spec for ``seed``.

        :param seed: Seed for all generation randomness; recorded in the spec.
        :return: A plain spec dict conforming to the building schema.
        """
        if self._footprint_shape == _RECT_SHAPE:
            return self._generate_rect(seed)
        return self._generate_shaped(seed)

    def _generate_rect(self, seed: int) -> dict:
        """The original single-rectangle path. Kept verbatim so output stays frozen."""
        rng = random.Random(seed)
        footprint = Rectangle(0.0, 0.0, self._width, self._depth)

        subdivision = BspSubdivider(self._num_rooms, self._min_room_size).subdivide(footprint, rng)
        exterior_walls = self._exterior_walls(footprint)
        interior_walls = self._interior_walls(subdivision)
        openings_by_wall = OpeningPlacer().place(exterior_walls, interior_walls)

        walls = exterior_walls + interior_walls
        for wall in walls:
            openings = openings_by_wall.get(wall["id"], [])
            if openings:
                wall["openings"] = openings

        logger.debug(
            "generated spec: seed=%d rooms=%d walls=%d", seed, len(subdivision.rooms), len(walls)
        )
        return {
            "schema_version": _SCHEMA_VERSION,
            "seed": seed,
            "units": "m",
            "storeys": [
                {
                    "elevation": 0.0,
                    "height": self._storey_height,
                    "walls": walls,
                    "rooms": self._rooms(subdivision),
                }
            ],
            "roof": {"kind": "flat", "thickness": _DEFAULT_ROOF_THICKNESS},
        }

    def _generate_shaped(self, seed: int) -> dict:
        """L/T/U footprint path: occupancy grid -> polygon -> walls/rooms (flat roof)."""
        if self._roof_kind != "flat":
            raise ValueError(
                f"roof kind {self._roof_kind!r} is not supported on a "
                f"{self._footprint_shape!r} footprint yet; only 'flat' (pitched roofs over "
                "non-rectangular footprints are deferred)"
            )
        rng = random.Random(seed)
        grid = FootprintGrid(self._footprint_shape, self._width, self._depth)
        polygon = grid.polygon()

        exterior_walls = self._exterior_walls_from_polygon(polygon)
        interior_walls, rooms = self._rooms_and_interior_walls(grid.wings(), rng)
        openings_by_wall = OpeningPlacer().place(exterior_walls, interior_walls)

        walls = exterior_walls + interior_walls
        for wall in walls:
            openings = openings_by_wall.get(wall["id"], [])
            if openings:
                wall["openings"] = openings

        logger.debug(
            "generated %s spec: seed=%d rooms=%d walls=%d",
            self._footprint_shape, seed, len(rooms), len(walls),
        )
        return {
            "schema_version": _SCHEMA_VERSION,
            "seed": seed,
            "units": "m",
            "storeys": [
                {
                    "elevation": 0.0,
                    "height": self._storey_height,
                    "walls": walls,
                    "rooms": rooms,
                    "footprint": [list(point) for point in polygon],
                }
            ],
            "roof": {"kind": "flat", "thickness": _DEFAULT_ROOF_THICKNESS},
        }

    def _exterior_walls_from_polygon(self, polygon: list) -> list[dict]:
        """One wall per polygon edge, reordered so the longest edge is first (front door)."""
        count = len(polygon)
        edges = [(polygon[i], polygon[(i + 1) % count]) for i in range(count)]
        longest = max(range(count), key=lambda i: _segment_length(edges[i]))
        ordered = edges[longest:] + edges[:longest]
        return [self._wall(f"ext_{i}", start, end) for i, (start, end) in enumerate(ordered)]

    def _rooms_and_interior_walls(self, wings: list[Rectangle], rng: random.Random):
        """BSP each wing into rooms; emit per-wing split walls + one seam wall per join."""
        total_area = sum(wing.area for wing in wings)
        rooms: list[dict] = []
        interior_walls: list[dict] = []
        room_index = 0
        wall_index = 0
        for wing in wings:
            wing_rooms = max(1, round(self._num_rooms * wing.area / total_area))
            subdivision = BspSubdivider(wing_rooms, self._min_room_size).subdivide(wing, rng)
            for room in subdivision.rooms:
                rooms.append(
                    {
                        "id": f"room_{room_index}",
                        "polygon": [list(point) for point in room.corners()],
                    }
                )
                room_index += 1
            for segment in subdivision.interior_walls:
                interior_walls.append(self._wall(f"interior_{wall_index}", segment[0], segment[1]))
                wall_index += 1
        interior_walls.extend(self._seam_walls(wings, start_index=wall_index))
        return interior_walls, rooms

    def _seam_walls(self, wings: list[Rectangle], start_index: int) -> list[dict]:
        """One door-bearing interior wall on each shared edge between adjacent wings."""
        seam_walls = []
        index = start_index
        for i in range(len(wings)):
            for j in range(i + 1, len(wings)):
                seam = _shared_edge(wings[i], wings[j])
                if seam is not None:
                    seam_walls.append(self._wall(f"interior_{index}", seam[0], seam[1]))
                    index += 1
        return seam_walls

    def _exterior_walls(self, footprint: Rectangle) -> list[dict]:
        """The four footprint edges as walls, counter-clockwise from the min corner."""
        corners = footprint.corners()
        names = ["ext_south", "ext_east", "ext_north", "ext_west"]
        walls = []
        for index, name in enumerate(names):
            start = corners[index]
            end = corners[(index + 1) % len(corners)]
            walls.append(self._wall(name, start, end))
        return walls

    def _interior_walls(self, subdivision: Subdivision) -> list[dict]:
        """Interior walls from the subdivision's split segments, with stable ids."""
        return [
            self._wall(f"interior_{index}", segment[0], segment[1])
            for index, segment in enumerate(subdivision.interior_walls)
        ]

    def _wall(self, wall_id: str, start, end) -> dict:
        return {
            "id": wall_id,
            "start": [start[0], start[1]],
            "end": [end[0], end[1]],
            "thickness": self._wall_thickness,
        }

    def _rooms(self, subdivision: Subdivision) -> list[dict]:
        return [
            {"id": f"room_{index}", "polygon": [list(point) for point in room.corners()]}
            for index, room in enumerate(subdivision.rooms)
        ]


def _segment_length(edge) -> float:
    (x0, y0), (x1, y1) = edge
    return math.hypot(x1 - x0, y1 - y0)


def _shared_edge(a: Rectangle, b: Rectangle):
    """The shared boundary segment between two adjacent axis-aligned rects, or None.

    Returns ``(start, end)`` along the common edge where the two rectangles touch with
    positive overlap (a vertical seam if they meet left/right, horizontal if top/bottom).
    """
    if a.x1 == b.x0 or b.x1 == a.x0:  # vertical seam (shared x line)
        x = a.x1 if a.x1 == b.x0 else a.x0
        lo, hi = max(a.y0, b.y0), min(a.y1, b.y1)
        if hi > lo:
            return (x, lo), (x, hi)
    if a.y1 == b.y0 or b.y1 == a.y0:  # horizontal seam (shared y line)
        y = a.y1 if a.y1 == b.y0 else a.y0
        lo, hi = max(a.x0, b.x0), min(a.x1, b.x1)
        if hi > lo:
            return (lo, y), (hi, y)
    return None
