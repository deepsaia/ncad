"""Compile a coarse, agent-authorable *brief* into a precise building spec.

The brief is the level of detail an LLM agent can reliably emit: round-number footprint
vertices, a map of which corners to round (by index) and how much, room count, storey
height, roof kind. The compiler does all the precise arithmetic — tangent points, arc
centers, exterior/arc walls, openings — producing a schema-valid spec the builder
consumes. This is the bridge to the agent layer (design.md §0, §6): agents describe
intent; the compiler turns it into geometry-ready data.

Brief shape::

    {
      "footprint": [[0, 0], [10, 0], [10, 8], [0, 8]],   # coarse CCW polygon (round numbers)
      "rounded_corners": {"1": 1.5, "3": 1.0},            # vertex index -> fillet radius
      "num_rooms": 4,                                     # best-effort interior subdivision
      "storey_height": 3.0,
      "roof": "flat",
    }
"""

import logging

from ncad.generate.corner_rounding import longest_wall_first, round_corners
from ncad.generate.opening_placer import OpeningPlacer

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = 1
_DEFAULT_THICKNESS = 0.2
_DEFAULT_STOREY_HEIGHT = 3.0
_DEFAULT_ROOF_THICKNESS = 0.2


class SpecCompiler:
    """Turns a coarse brief into a precise, schema-valid building spec dict."""

    def compile(self, brief: dict) -> dict:
        """Compile ``brief`` into a building spec.

        :param brief: Coarse intent (see module docstring).
        :return: A schema-valid spec dict ready for the builder.
        :raises ValueError: If the footprint is missing or has fewer than 3 vertices.
        """
        polygon = [tuple(point) for point in brief.get("footprint", [])]
        if len(polygon) < 3:
            raise ValueError("brief footprint must have at least 3 vertices")
        thickness = brief.get("wall_thickness", _DEFAULT_THICKNESS)
        storey_height = brief.get("storey_height", _DEFAULT_STOREY_HEIGHT)
        radii = {int(index): radius for index, radius in brief.get("rounded_corners", {}).items()}

        rounded = round_corners(polygon, radii, thickness)
        straight_walls = longest_wall_first(rounded["straight_walls"])
        arc_walls = rounded["arc_walls"]

        openings_by_wall = OpeningPlacer().place(straight_walls, interior_walls=[])
        walls = straight_walls + arc_walls
        for wall in walls:
            openings = openings_by_wall.get(wall["id"], [])
            if openings:
                wall["openings"] = openings

        rooms = [{"id": "room_0", "polygon": [list(point) for point in polygon]}]
        logger.info(
            "compiled brief: %d-vertex footprint, %d rounded corner(s), %d walls",
            len(polygon), len(radii), len(walls),
        )
        return {
            "schema_version": _SCHEMA_VERSION,
            "seed": 0,
            "units": "m",
            "storeys": [
                {
                    "elevation": 0.0,
                    "height": storey_height,
                    "walls": walls,
                    "rooms": rooms,
                    "footprint": rounded["footprint"],
                }
            ],
            "roof": {"kind": brief.get("roof", "flat"), "thickness": _DEFAULT_ROOF_THICKNESS},
        }
