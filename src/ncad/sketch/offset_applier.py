"""Expand ``offset`` sketch entries into real derived entities.

An offset takes a source entity (often a projected construction line/arc/circle) and
produces a NEW real (non-construction) entity offset from it: a line offset parallel by a
signed distance, or a circle/arc of radius +/- distance. The offset is computed from the
source's seed geometry, so a projected (fixed) source gives an exact offset. Non-offset
entities pass through unchanged.
"""

import logging
import math

logger = logging.getLogger(__name__)


class OffsetError(Exception):
    """An offset references an unknown or unsupported source entity."""


class OffsetApplier:
    """Expands offset entries into real derived entities."""

    def apply(self, entities: list[dict]) -> list[dict]:
        """Return ``entities`` with each ``offset`` entry expanded to a real entity."""
        by_id = {e["id"]: e for e in entities if "id" in e}
        out: list[dict] = []
        for entity in entities:
            if entity.get("type") != "offset":
                out.append(entity)
                continue
            out.extend(_expand_offset(entity, by_id))
        return out


def _expand_offset(offset: dict, by_id: dict) -> list[dict]:
    """The real entities for one offset entry."""
    source = by_id.get(offset.get("from"))
    if source is None:
        raise OffsetError(f"offset {offset.get('id')!r} references unknown entity "
                          f"{offset.get('from')!r}")
    distance = float(offset["distance"])
    oid = offset["id"]
    stype = source["type"]
    if stype == "line":
        return _offset_line(oid, source, by_id, distance)
    if stype in ("circle", "arc"):
        return _offset_curve(oid, source, distance)
    raise OffsetError(f"cannot offset a {stype!r} (offset {oid!r})")


def _offset_line(oid: str, source: dict, by_id: dict, distance: float) -> list[dict]:
    """A parallel line offset from ``source`` by ``distance`` along its left normal."""
    ax, ay = by_id[source["p1"]]["at"]
    bx, by = by_id[source["p2"]]["at"]
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-12:
        raise OffsetError(f"cannot offset a zero-length line (offset {oid!r})")
    nx, ny = -dy / length, dx / length
    ox, oy = nx * distance, ny * distance
    return [
        {"id": f"{oid}/a", "type": "point", "at": [ax + ox, ay + oy]},
        {"id": f"{oid}/b", "type": "point", "at": [bx + ox, by + oy]},
        {"id": oid, "type": "line", "p1": f"{oid}/a", "p2": f"{oid}/b"},
    ]


def _offset_curve(oid: str, source: dict, distance: float) -> list[dict]:
    """A concentric circle/arc of radius +/- distance, sharing the source center."""
    new_radius = float(source.get("radius", 0.0)) + distance
    result = {"id": oid, "type": source["type"], "center": source["center"],
              "radius": new_radius}
    if source["type"] == "arc":
        result["start"] = source["start"]
        result["end"] = source["end"]
    return [result]
