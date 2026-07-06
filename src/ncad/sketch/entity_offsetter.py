"""Offset a single primitive sketch entity by a signed distance.

A line offsets to a parallel line along its left normal (-dy, dx)/len (matching
OffsetApplier's convention); a circle or arc offsets to a concentric one with radius
+/- distance and a fresh center point. Results are fixed primitives, namespaced under a
caller-supplied prefix. Pure: no randomness, no mutation of inputs. Shared by loop_offset
(offset every edge) and arc-corner fillet (offset both entities to find the arc center).
"""

import logging
import math

from ncad.sketch.arc_geometry import seed_radius

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
    """A concentric circle/arc with radius +/- distance and a fresh center point.

    A circle keeps its explicit radius. An arc additionally gets fresh start/end points
    on the new radius (same angles as the source), so the returned arc is self-consistent
    (radius == center-to-endpoint distance) even when used standalone, rather than reusing
    the source endpoints that still sit on the old radius.
    """
    seeds = {pid: (float(e["at"][0]), float(e["at"][1]))
             for pid, e in by_id.items() if e.get("type") == "point"}
    cx, cy = seeds[curve["center"]]
    new_radius = seed_radius(curve, seeds) + distance
    if new_radius <= 1e-12:
        raise ValueError(f"offset collapses curve {curve['id']!r} (radius {new_radius})")
    center = {"id": f"{prefix}/c", "type": "point", "at": [cx, cy], "fixed": True}
    result = {"id": prefix, "type": curve["type"], "center": f"{prefix}/c",
              "radius": new_radius, "fixed": True}
    if curve["type"] != "arc":
        return [center, result]
    start = _radial_point(cx, cy, seeds[curve["start"]], new_radius, f"{prefix}/s")
    end = _radial_point(cx, cy, seeds[curve["end"]], new_radius, f"{prefix}/e")
    result["start"], result["end"] = start["id"], end["id"]
    return [center, start, end, result]


def _radial_point(cx: float, cy: float, source: tuple[float, float], radius: float,
                  pid: str) -> dict:
    """A fixed point at ``radius`` from (cx, cy) along the direction to ``source``."""
    ang = math.atan2(source[1] - cy, source[0] - cx)
    return {"id": pid, "type": "point", "at": [cx + radius * math.cos(ang),
                                               cy + radius * math.sin(ang)],
            "fixed": True}
