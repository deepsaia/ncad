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
        self._corner_radius = params.get("corner_radius", 0.0)

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

        if self._corner_radius > 0:
            straight_walls, arc_walls, footprint = self._rounded_exterior(polygon)
        else:
            straight_walls = self._exterior_walls_from_polygon(polygon)
            arc_walls = []
            footprint = [list(point) for point in polygon]

        interior_walls, rooms = self._rooms_and_interior_walls(grid.wings(), rng)
        # Only straight exterior + interior walls get openings; arc corner pieces don't.
        openings_by_wall = OpeningPlacer().place(straight_walls, interior_walls)

        walls = straight_walls + arc_walls + interior_walls
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
                    "footprint": footprint,
                }
            ],
            "roof": {"kind": "flat", "thickness": _DEFAULT_ROOF_THICKNESS},
        }

    def _rounded_exterior(self, polygon: list):
        """Round convex corners: straight walls between tangent points + arc corner walls.

        Returns ``(straight_walls, arc_walls, footprint)`` where footprint mixes plain
        points (sharp corners) and object vertices (rounded). The radius is clamped per
        corner to half the shorter adjacent edge so the fillet never overruns an edge.
        """
        count = len(polygon)
        # Per-vertex: (tangent_in, tangent_out, radius) for rounded corners, else None.
        plans = [self._corner_plan(polygon, i) for i in range(count)]

        straight_walls = []
        arc_walls = []
        footprint = []
        wall_index = 0
        for i in range(count):
            corner = polygon[i]
            plan = plans[i]
            # Footprint vertex: object form if rounded, else plain point.
            if plan is None:
                footprint.append(list(corner))
            else:
                footprint.append({"point": list(corner), "corner_radius": plan[2]})
            # Straight edge from this corner's exit point to the next corner's entry point.
            start = plan[1] if plan is not None else corner
            next_plan = plans[(i + 1) % count]
            next_corner = polygon[(i + 1) % count]
            end = next_plan[0] if next_plan is not None else next_corner
            straight_walls.append(self._wall(f"ext_{wall_index}", start, end))
            wall_index += 1
            # Arc wall turning this corner (between tangent_in and tangent_out).
            if plan is not None:
                arc_walls.append(self._corner_arc_wall(f"ext_arc_{i}", corner, plan))

        # Front door on the longest straight edge.
        straight_walls = _longest_first(straight_walls)
        return straight_walls, arc_walls, footprint

    def _corner_plan(self, polygon: list, i: int):
        """Rounding plan for any corner: (tangent_in, tangent_out, radius, convex), or None.

        Both convex (outward, left-turn) and concave (inward, right-turn) corners round;
        the tangent-setback math is identical, only the arc sweep direction flips.
        """
        count = len(polygon)
        prev_pt, corner, next_pt = polygon[(i - 1) % count], polygon[i], polygon[(i + 1) % count]
        turn = _cross(prev_pt, corner, next_pt)
        if turn == 0:  # colinear — no corner to round
            return None
        convex = turn > 0
        in_len = _dist(prev_pt, corner)
        out_len = _dist(corner, next_pt)
        radius = min(self._corner_radius, 0.5 * min(in_len, out_len))
        if radius <= 0:
            return None
        setback = radius / math.tan(_half_angle(prev_pt, corner, next_pt))
        setback = min(setback, 0.5 * in_len, 0.5 * out_len)
        tan_in = _along(corner, prev_pt, setback)
        tan_out = _along(corner, next_pt, setback)
        return tan_in, tan_out, radius, convex

    def _corner_arc_wall(self, wall_id: str, corner, plan) -> dict:
        tan_in, tan_out, radius, convex = plan
        return {
            "id": wall_id,
            "start": [tan_in[0], tan_in[1]],
            "end": [tan_out[0], tan_out[1]],
            "thickness": self._wall_thickness,
            # Convex corners arc outward (CCW from in->out); concave arc inward (CW).
            "arc": {"center": list(_arc_center(corner, plan)), "clockwise": not convex},
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


def _longest_first(walls: list[dict]) -> list[dict]:
    """Rotate the wall list so the longest wall is first (keeps the front door valid)."""
    longest = max(range(len(walls)), key=lambda i: _dist(walls[i]["start"], walls[i]["end"]))
    return walls[longest:] + walls[:longest]


def _dist(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _cross(prev_pt, corner, next_pt) -> float:
    """Z of (corner-prev) x (next-corner); >0 = convex left turn on a CCW polygon."""
    return (corner[0] - prev_pt[0]) * (next_pt[1] - corner[1]) - (
        corner[1] - prev_pt[1]
    ) * (next_pt[0] - corner[0])


def _unit(frm, to) -> tuple:
    length = _dist(frm, to) or 1.0
    return ((to[0] - frm[0]) / length, (to[1] - frm[1]) / length)


def _along(frm, toward, distance) -> tuple:
    u = _unit(frm, toward)
    return (frm[0] + u[0] * distance, frm[1] + u[1] * distance)


def _half_angle(prev_pt, corner, next_pt) -> float:
    """Half the interior angle at ``corner`` between its two edges."""
    u_in = _unit(corner, prev_pt)
    u_out = _unit(corner, next_pt)
    cos_full = max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))
    return math.acos(cos_full) / 2.0


def _arc_center(corner, plan) -> tuple:
    """Fillet arc center: along the corner's angle bisector at radius / sin(half)."""
    tan_in, tan_out, radius, _convex = plan
    # Bisector direction = sum of the two edge unit vectors from the corner.
    u_in = _unit(corner, tan_in)
    u_out = _unit(corner, tan_out)
    bisector = (u_in[0] + u_out[0], u_in[1] + u_out[1])
    blen = math.hypot(*bisector) or 1.0
    half = math.acos(max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))) / 2.0
    center_dist = radius / math.sin(half)
    return (corner[0] + bisector[0] / blen * center_dist,
            corner[1] + bisector[1] / blen * center_dist)
