"""Pure 2D intersection math for sketch-modify topology operations.

Computes the intersection points of two primitive entities (line/arc/circle) from their
seed coordinates, treating a line as an infinite line for trim/extend/corner purposes
(the topology layer decides which points are relevant). An arc is a circle plus an
angular-range filter. Results are returned deterministically ordered (by x then y) so
downstream selection is stable. No randomness, no mutation of inputs.
"""

import logging
import math

from ncad.sketch.arc_geometry import arc_contains, seed_radius

logger = logging.getLogger(__name__)

_EPS = 1e-9


class GeometryIntersector:
    """Computes 2D intersection points between two primitive sketch entities."""

    def intersect(self, a: dict, b: dict,
                  points: dict[str, tuple[float, float]]) -> list[tuple[float, float]]:
        """Return the ordered intersection points of ``a`` and ``b`` from ``points``."""
        ta, tb = a["type"], b["type"]
        if ta == "line" and tb == "line":
            hits = _line_line(a, b, points)
        elif ta == "line" and tb in ("circle", "arc"):
            hits = _line_circle(a, b, points)
        elif ta in ("circle", "arc") and tb == "line":
            hits = _line_circle(b, a, points)
        elif ta in ("circle", "arc") and tb in ("circle", "arc"):
            hits = _circle_circle(a, b, points)
        else:
            hits = []
        return sorted(hits)


def _endpoints_xy(line: dict, points: dict) -> tuple[float, float, float, float]:
    """The (x1, y1, x2, y2) seed coordinates of a line's two endpoints."""
    x1, y1 = points[line["p1"]]
    x2, y2 = points[line["p2"]]
    return x1, y1, x2, y2


def _line_line(a: dict, b: dict, points: dict) -> list[tuple[float, float]]:
    """Intersection of two infinite lines through the given segments' endpoints."""
    x1, y1, x2, y2 = _endpoints_xy(a, points)
    x3, y3, x4, y4 = _endpoints_xy(b, points)
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < _EPS:
        return []
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return [(px, py)]


def _line_circle(line: dict, circle: dict, points: dict) -> list[tuple[float, float]]:
    """Intersections of an infinite line with a circle/arc (arc range filtered later)."""
    x1, y1, x2, y2 = _endpoints_xy(line, points)
    cx, cy = points[circle["center"]]
    radius = seed_radius(circle, points)
    dx, dy = x2 - x1, y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < _EPS:
        return []
    # Project circle center onto the line, then step +/- along the line by the half-chord.
    t = ((cx - x1) * dx + (cy - y1) * dy) / seg_len_sq
    foot_x, foot_y = x1 + t * dx, y1 + t * dy
    dist_sq = (foot_x - cx) ** 2 + (foot_y - cy) ** 2
    if dist_sq > radius * radius + _EPS:
        return []
    half_chord_sq = max(0.0, radius * radius - dist_sq)
    if half_chord_sq < _EPS:
        return _arc_filter(circle, [(foot_x, foot_y)], points)
    step = math.sqrt(half_chord_sq / seg_len_sq)
    hits = [(foot_x - step * dx, foot_y - step * dy),
            (foot_x + step * dx, foot_y + step * dy)]
    return _arc_filter(circle, hits, points)


def _circle_circle(a: dict, b: dict, points: dict) -> list[tuple[float, float]]:
    """Intersections of two circles/arcs (each operand's arc range filtered)."""
    ax, ay = points[a["center"]]
    bx, by = points[b["center"]]
    ra, rb = seed_radius(a, points), seed_radius(b, points)
    d = math.hypot(bx - ax, by - ay)
    if d < _EPS or d > ra + rb + _EPS or d < abs(ra - rb) - _EPS:
        return []
    aa = (ra * ra - rb * rb + d * d) / (2 * d)
    h_sq = max(0.0, ra * ra - aa * aa)
    mx, my = ax + aa * (bx - ax) / d, ay + aa * (by - ay) / d
    if h_sq < _EPS:
        hits = [(mx, my)]
    else:
        h = math.sqrt(h_sq)
        ox, oy = -(by - ay) / d * h, (bx - ax) / d * h
        hits = [(mx + ox, my + oy), (mx - ox, my - oy)]
    return _arc_filter(a, _arc_filter(b, hits, points), points)


def _arc_filter(entity: dict, hits: list[tuple[float, float]],
                points: dict) -> list[tuple[float, float]]:
    """Drop intersection points outside an arc's CCW span (circles keep all).

    Endpoints are inclusive: an intersection exactly at an arc tip is a real hit.
    """
    if entity["type"] != "arc":
        return hits
    return [h for h in hits if arc_contains(entity, h, points, inclusive=True)]
