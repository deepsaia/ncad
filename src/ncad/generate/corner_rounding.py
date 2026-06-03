"""Pure corner-rounding geometry: a coarse polygon + per-corner radii -> exact walls.

Given a footprint polygon (round-number vertices) and a map of vertex index -> desired
fillet radius, this computes the precise architectural pieces the builder needs:
straight wall segments between tangent points, arc walls turning each rounded corner, and
the footprint vertex list (plain points for sharp corners, ``{point, corner_radius}`` for
rounded ones). All the fiddly tangent/arc-center arithmetic lives here so callers — the
``Generator`` and the agent-facing ``SpecCompiler`` — describe *intent* (which corners,
how round) and never hand-author precise coordinates.

Both convex (outward) and concave (inward) corners round; the tangent-setback math is
identical and only the arc sweep direction differs (recorded as ``clockwise``).
"""

import math

Point = tuple[float, float]


def round_corners(polygon: list[Point], radii: dict[int, float], thickness: float) -> dict:
    """Compile a polygon + per-corner radii into walls + footprint.

    :param polygon: Ordered CCW boundary vertices (round numbers are fine).
    :param radii: Map of vertex index -> requested fillet radius (clamped per corner).
    :param thickness: Wall thickness (m) applied to every emitted wall.
    :return: ``{"straight_walls": [...], "arc_walls": [...], "footprint": [...]}`` where
        walls are spec wall dicts (ids ``ext_*`` / ``ext_arc_*``) and footprint mixes
        plain ``[x, y]`` (sharp) and ``{"point", "corner_radius"}`` (rounded) vertices.
    """
    count = len(polygon)
    plans = [_corner_plan(polygon, i, radii.get(i, 0.0)) for i in range(count)]

    straight_walls = []
    arc_walls = []
    footprint = []
    for i in range(count):
        corner = polygon[i]
        plan = plans[i]
        if plan is None:
            footprint.append([corner[0], corner[1]])
        else:
            footprint.append({"point": [corner[0], corner[1]], "corner_radius": plan["radius"]})
        start = plan["tan_out"] if plan is not None else corner
        next_plan = plans[(i + 1) % count]
        next_corner = polygon[(i + 1) % count]
        end = next_plan["tan_in"] if next_plan is not None else next_corner
        straight_walls.append(_wall(f"ext_{i}", start, end, thickness))
        if plan is not None:
            arc_walls.append(_arc_wall(f"ext_arc_{i}", corner, plan, thickness))

    return {"straight_walls": straight_walls, "arc_walls": arc_walls, "footprint": footprint}


def _corner_plan(polygon: list[Point], i: int, requested_radius: float):
    """Rounding plan for one corner, or None if it stays sharp."""
    if requested_radius <= 0:
        return None
    count = len(polygon)
    prev_pt, corner, next_pt = polygon[(i - 1) % count], polygon[i], polygon[(i + 1) % count]
    turn = _cross(prev_pt, corner, next_pt)
    if turn == 0:  # colinear — not a corner
        return None
    in_len = _dist(prev_pt, corner)
    out_len = _dist(corner, next_pt)
    radius = min(requested_radius, 0.5 * min(in_len, out_len))
    if radius <= 0:
        return None
    setback = radius / math.tan(_half_angle(prev_pt, corner, next_pt))
    setback = min(setback, 0.5 * in_len, 0.5 * out_len)
    return {
        "tan_in": _along(corner, prev_pt, setback),
        "tan_out": _along(corner, next_pt, setback),
        "radius": radius,
        "convex": turn > 0,
    }


def _wall(wall_id: str, start: Point, end: Point, thickness: float) -> dict:
    return {
        "id": wall_id,
        "start": [start[0], start[1]],
        "end": [end[0], end[1]],
        "thickness": thickness,
    }


def _arc_wall(wall_id: str, corner: Point, plan: dict, thickness: float) -> dict:
    tan_in, tan_out = plan["tan_in"], plan["tan_out"]
    return {
        "id": wall_id,
        "start": [tan_in[0], tan_in[1]],
        "end": [tan_out[0], tan_out[1]],
        "thickness": thickness,
        # Convex corners arc outward (CCW from in->out); concave arc inward (CW).
        "arc": {"center": list(_arc_center(corner, plan)), "clockwise": not plan["convex"]},
    }


def longest_wall_first(walls: list[dict]) -> list[dict]:
    """Rotate the wall list so the longest wall is first (keeps the front door valid)."""
    longest = max(range(len(walls)), key=lambda i: _dist(walls[i]["start"], walls[i]["end"]))
    return walls[longest:] + walls[:longest]


def _dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _cross(prev_pt: Point, corner: Point, next_pt: Point) -> float:
    """Z of (corner-prev) x (next-corner); >0 = convex left turn on a CCW polygon."""
    return (corner[0] - prev_pt[0]) * (next_pt[1] - corner[1]) - (
        corner[1] - prev_pt[1]
    ) * (next_pt[0] - corner[0])


def _unit(frm: Point, to: Point) -> Point:
    length = _dist(frm, to) or 1.0
    return ((to[0] - frm[0]) / length, (to[1] - frm[1]) / length)


def _along(frm: Point, toward: Point, distance: float) -> Point:
    u = _unit(frm, toward)
    return (frm[0] + u[0] * distance, frm[1] + u[1] * distance)


def _half_angle(prev_pt: Point, corner: Point, next_pt: Point) -> float:
    """Half the interior angle at ``corner`` between its two edges."""
    u_in = _unit(corner, prev_pt)
    u_out = _unit(corner, next_pt)
    cos_full = max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))
    return math.acos(cos_full) / 2.0


def _arc_center(corner: Point, plan: dict) -> Point:
    """Fillet arc center: along the corner's angle bisector at radius / sin(half)."""
    u_in = _unit(corner, plan["tan_in"])
    u_out = _unit(corner, plan["tan_out"])
    bisector = (u_in[0] + u_out[0], u_in[1] + u_out[1])
    blen = math.hypot(*bisector) or 1.0
    half = math.acos(max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))) / 2.0
    center_dist = plan["radius"] / math.sin(half)
    return (corner[0] + bisector[0] / blen * center_dist,
            corner[1] + bisector[1] / blen * center_dist)
