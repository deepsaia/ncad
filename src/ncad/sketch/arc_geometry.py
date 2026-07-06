"""Shared 2D arc/circle geometry helpers for the sketch layer.

A circle carries an explicit ``radius``; an arc's radius is the center-to-start seed
distance. Whether a point lies within an arc's CCW span (start to end) is used both to
filter intersection candidates (endpoints inclusive) and to validate a split location
(endpoints exclusive), so ``arc_contains`` takes an ``inclusive`` flag. All functions
operate on a ``seeds`` map of point id -> (x, y). Pure: no mutation, no randomness.
"""

import math

_EPS = 1e-9


def seed_radius(curve: dict, seeds: dict[str, tuple[float, float]]) -> float:
    """A circle's explicit radius, or an arc's center-to-start seed distance."""
    if "radius" in curve:
        return float(curve["radius"])
    cx, cy = seeds[curve["center"]]
    sx, sy = seeds[curve["start"]]
    return math.hypot(sx - cx, sy - cy)


def arc_contains(arc: dict, point: tuple[float, float],
                 seeds: dict[str, tuple[float, float]], inclusive: bool) -> bool:
    """Whether ``point`` lies within ``arc``'s CCW span from start to end.

    ``inclusive`` keeps points exactly at the span endpoints (used when filtering
    intersection candidates); the exclusive form (used to validate a split point) rejects
    the endpoints so a cut cannot land on an existing vertex.
    """
    cx, cy = seeds[arc["center"]]
    sx, sy = seeds[arc["start"]]
    ex, ey = seeds[arc["end"]]
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    ap = math.atan2(point[1] - cy, point[0] - cx)
    span = (a1 - a0) % (2 * math.pi)
    rel = (ap - a0) % (2 * math.pi)
    if inclusive:
        return rel <= span + _EPS
    return _EPS < rel < span - _EPS
