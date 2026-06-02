"""Generate a building spec from a seed and parameters.

This is the one place randomness lives: ``generate`` seeds a single ``random.Random``
from ``seed`` and threads it into the subdivider. Same ``(seed, params)`` therefore
yields an identical spec (golden-spec determinism, design.md §0). The output is a plain
dict conforming to ``schema/building_schema.hocon``.
"""

import logging
import random

from ncad.generate.bsp_subdivider import BspSubdivider
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

    def generate(self, seed: int) -> dict:
        """Generate the spec for ``seed``.

        :param seed: Seed for all generation randomness; recorded in the spec.
        :return: A plain spec dict conforming to the building schema.
        """
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
