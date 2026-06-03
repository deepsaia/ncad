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
import math

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
        num_storeys = max(1, int(brief.get("num_storeys", 1)))

        # Stack identical footprints; each storey gets its own freshly-built wall dicts so
        # opening lists never alias across floors.
        storeys = [
            self._build_storey_dict(
                polygon, radii, thickness, storey_height,
                elevation=i * storey_height, is_ground=(i == 0),
            )
            for i in range(num_storeys)
        ]
        self._apply_balconies(brief.get("balconies", []), storeys, storey_height)
        logger.info(
            "compiled brief: %d-vertex footprint, %d rounded corner(s), %d storey(s)",
            len(polygon), len(radii), num_storeys,
        )
        return {
            "schema_version": _SCHEMA_VERSION,
            "seed": 0,
            "units": "m",
            "storeys": storeys,
            "roof": {"kind": brief.get("roof", "flat"), "thickness": _DEFAULT_ROOF_THICKNESS},
        }

    def _build_storey_dict(self, polygon, radii, thickness, storey_height, elevation, is_ground):
        """One storey dict: exterior + arc walls (with openings) + room + footprint.

        Only the ground floor gets the front door (it opens onto the ground). Upper floors
        keep windows but drop exterior doors — an upper exterior door needs a balcony to
        open onto, which is added separately by :meth:`_apply_balconies`.
        """
        rounded = round_corners(polygon, radii, thickness)
        straight_walls = longest_wall_first(rounded["straight_walls"])
        arc_walls = rounded["arc_walls"]

        openings_by_wall = OpeningPlacer().place(straight_walls, interior_walls=[])
        walls = straight_walls + arc_walls
        for wall in walls:
            openings = openings_by_wall.get(wall["id"], [])
            if not is_ground:
                openings = [o for o in openings if o["kind"] != "door"]
            if openings:
                wall["openings"] = openings

        return {
            "elevation": elevation,
            "height": storey_height,
            "walls": walls,
            "rooms": [{"id": "room_0", "polygon": [list(point) for point in polygon]}],
            "footprint": rounded["footprint"],
        }

    def _apply_balconies(self, balconies: list, storeys: list, storey_height: float) -> None:
        """Attach balconies to their storeys and add a paired tall opening on each wall.

        A balcony forces a door-like opening on its wall: width = balcony length, height =
        0.9 * storey height, sill 0 (access onto the balcony floor). Balconies are only
        valid on upper storeys (index >= 1) — never a ground-floor-only / single-storey
        building.
        """
        for balcony in balconies:
            index = int(balcony.get("storey", 0))
            if index == 0:
                raise ValueError(
                    "balconies are not allowed on the ground floor (storey 0); "
                    "they require an upper storey"
                )
            if index >= len(storeys):
                raise ValueError(
                    f"balcony references storey {index}, but only {len(storeys)} exist"
                )
            storey = storeys[index]
            exterior = [w for w in storey["walls"] if "arc" not in w]
            wall = exterior[int(balcony["wall"]) % len(exterior)]
            length, depth, along = balcony["length"], balcony["depth"], balcony.get("along", 0.5)

            # Paired tall access opening on the balcony wall.
            wall.setdefault("openings", [])
            wall["openings"] = self._without_overlap(wall, along, length)
            wall["openings"].append(
                {
                    "id": f"{wall['id']}_balcony_door",
                    "kind": "door",
                    "along": along,
                    "width": length,
                    "height": round(0.9 * storey_height, 3),
                    "sill": 0.0,
                }
            )
            storey.setdefault("balconies", []).append(
                {"wall_id": wall["id"], "along": along, "length": length, "depth": depth}
            )

    def _without_overlap(self, wall: dict, along: float, width: float) -> list:
        """Drop existing openings whose span overlaps the new opening at ``along``/``width``."""
        length = math.hypot(
            wall["end"][0] - wall["start"][0], wall["end"][1] - wall["start"][1]
        ) or 1.0
        lo, hi = along * length - width / 2, along * length + width / 2
        kept = []
        for opening in wall.get("openings", []):
            c = opening["along"] * length
            o_lo, o_hi = c - opening["width"] / 2, c + opening["width"] / 2
            if o_hi <= lo or o_lo >= hi:  # disjoint
                kept.append(opening)
        return kept
