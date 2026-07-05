"""Offset a single primitive sketch entity by a signed distance.

A line offsets to a parallel line along its left normal (-dy, dx)/len (matching
OffsetApplier's convention); a circle or arc offsets to a concentric one with radius
+/- distance and a fresh center point. Results are fixed primitives, namespaced under a
caller-supplied prefix. Pure: no randomness, no mutation of inputs. Shared by loop_offset
(offset every edge) and arc-corner fillet (offset both entities to find the arc center).
"""

import logging
import math

logger = logging.getLogger(__name__)


class EntityOffsetter:
    """Computes the offset of one primitive entity by a signed distance."""

    def offset(self, entity: dict, by_id: dict, distance: float,
               prefix: str) -> list[dict]:
        """Return the fixed offset primitive(s) for ``entity`` shifted by ``distance``."""
        etype = entity["type"]
        if etype == "line":
            return _offset_line(entity, by_id, distance, prefix)
        if etype in ("circle", "arc"):
            return _offset_curve(entity, by_id, distance, prefix)
        raise ValueError(f"cannot offset a {etype!r} entity")


def _offset_line(line: dict, by_id: dict, distance: float, prefix: str) -> list[dict]:
    """A parallel line offset along the left normal by ``distance``."""
    ax, ay = by_id[line["p1"]]["at"]
    bx, by = by_id[line["p2"]]["at"]
    dx, dy = float(bx) - float(ax), float(by) - float(ay)
    length = math.hypot(dx, dy)
    if length < 1e-12:
        raise ValueError(f"cannot offset zero-length line {line['id']!r}")
    nx, ny = -dy / length, dx / length
    ox, oy = nx * distance, ny * distance
    return [
        {"id": f"{prefix}/a", "type": "point", "at": [float(ax) + ox, float(ay) + oy],
         "fixed": True},
        {"id": f"{prefix}/b", "type": "point", "at": [float(bx) + ox, float(by) + oy],
         "fixed": True},
        {"id": prefix, "type": "line", "p1": f"{prefix}/a", "p2": f"{prefix}/b",
         "fixed": True},
    ]


def _offset_curve(curve: dict, by_id: dict, distance: float, prefix: str) -> list[dict]:
    """A concentric circle/arc with radius +/- distance and a fresh center point."""
    cx, cy = by_id[curve["center"]]["at"]
    radius = _seed_radius(curve, by_id)
    new_radius = radius + distance
    if new_radius <= 1e-12:
        raise ValueError(f"offset collapses curve {curve['id']!r} (radius {new_radius})")
    center = {"id": f"{prefix}/c", "type": "point", "at": [float(cx), float(cy)],
              "fixed": True}
    result = {"id": prefix, "type": curve["type"], "center": f"{prefix}/c",
              "radius": new_radius, "fixed": True}
    if curve["type"] == "arc":
        result["start"] = curve["start"]
        result["end"] = curve["end"]
    return [center, result]


def _seed_radius(curve: dict, by_id: dict) -> float:
    """A circle's explicit radius, or an arc's center-to-start seed distance."""
    if "radius" in curve:
        return float(curve["radius"])
    cx, cy = by_id[curve["center"]]["at"]
    sx, sy = by_id[curve["start"]]["at"]
    return math.hypot(float(sx) - float(cx), float(sy) - float(cy))
