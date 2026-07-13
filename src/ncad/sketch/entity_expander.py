"""Lower sugar sketch entities to primitive point/line/arc entities before solving.

`polyline`, `slot`, and regular `polygon` are author conveniences; the solver and wire
builder only understand primitive `point`/`line`/`arc`/`circle` entities. This class
expands the sugar deterministically (child ids are ``<id>/<tag><index>``, no randomness)
and passes primitives through unchanged. Child-point seeds are derived from the
referenced points' ``at`` seeds plus the sugar's own numeric seeds; the solver then
refines them under any constraints.
"""

import logging
import math

from ncad.sketch.id_padding import PaddedNaming

logger = logging.getLogger(__name__)

_PASSTHROUGH = frozenset({"point", "line", "arc", "circle"})


class EntityExpander:
    """Expands sugar entities (polyline/slot/polygon) into primitives."""

    def __init__(self) -> None:
        self._naming = PaddedNaming()

    def expand(self, entities: list[dict]) -> list[dict]:
        """Return a new entity list with sugar lowered to primitives."""
        by_id = {e["id"]: e for e in entities}
        out: list[dict] = []
        for entity in entities:
            kind = entity.get("type")
            if kind in _PASSTHROUGH:
                out.append(entity)
            elif kind == "polyline":
                out.extend(self._expand_polyline(entity))
            elif kind == "polygon":
                out.extend(self._expand_polygon(entity, by_id))
            elif kind == "slot":
                out.extend(self._expand_slot(entity, by_id))
            elif kind == "arc_polar":
                out.extend(self._expand_arc_polar(entity, by_id))
            else:
                logger.debug("passing through unknown entity type %r", kind)
                out.append(entity)
        return out

    def _expand_polyline(self, entity: dict) -> list[dict]:
        """A polyline is an open chain of lines between consecutive point ids."""
        points = entity["points"]
        line_ids = self._naming.child_ids(f"{entity['id']}/l", len(points) - 1)
        return [{"id": line_ids[i], "type": "line", "p1": points[i], "p2": points[i + 1]}
                for i in range(len(points) - 1)]

    def _expand_polygon(self, entity: dict, by_id: dict) -> list[dict]:
        """A regular polygon: n points on a circle about the center, joined by n lines."""
        sid = entity["id"]
        sides = int(entity["sides"])
        radius = float(entity["r"])
        cx, cy = _seed_of(by_id, entity["center"])
        point_ids = self._naming.child_ids(f"{sid}/p", sides)
        line_ids = self._naming.child_ids(f"{sid}/l", sides)
        result: list[dict] = []
        for i in range(sides):
            angle = 2.0 * math.pi * i / sides
            result.append({"id": point_ids[i], "type": "point",
                           "at": [cx + radius * math.cos(angle), cy + radius * math.sin(angle)]})
        for i in range(sides):
            result.append({"id": line_ids[i], "type": "line",
                           "p1": point_ids[i], "p2": point_ids[(i + 1) % sides]})
        return result

    def _expand_arc_polar(self, entity: dict, by_id: dict) -> list[dict]:
        """A polar arc: center + radius + start_angle + sweep >> a three-point arc.

        Radius and the angles stay authoring inputs that seed the two endpoint points; a
        driven ``radius`` constraint (authored on the generated arc id) keeps them in the
        constraint layer, matching how polygon/slot lower to seeded primitives.
        """
        aid = entity["id"]
        cx, cy = _seed_of(by_id, entity["center"])
        radius = float(entity["radius"])
        start_angle = math.radians(float(entity["start_angle"]))
        end_angle = math.radians(float(entity["start_angle"]) + float(entity["sweep"]))
        start = (cx + radius * math.cos(start_angle), cy + radius * math.sin(start_angle))
        end = (cx + radius * math.cos(end_angle), cy + radius * math.sin(end_angle))
        return [
            {"id": f"{aid}/start", "type": "point", "at": [start[0], start[1]]},
            {"id": f"{aid}/end", "type": "point", "at": [end[0], end[1]]},
            {"id": aid, "type": "arc", "center": entity["center"],
             "start": f"{aid}/start", "end": f"{aid}/end"},
        ]

    def _expand_slot(self, entity: dict, by_id: dict) -> list[dict]:
        """A straight slot: two side lines plus two semicircular end caps.

        Given center points a (p1) and b (p2) and a width, the four corner points sit at
        +/- half-width perpendicular to the a->b axis. The caps are CCW arcs whose mids
        bulge outward (arc a mid points away from b; arc b mid points away from a).
        """
        sid = entity["id"]
        ax, ay = _seed_of(by_id, entity["p1"])
        bx, by = _seed_of(by_id, entity["p2"])
        half = float(entity["width"]) / 2.0
        px, py = _unit_perpendicular(ax, ay, bx, by)
        ox, oy = px * half, py * half
        # Corner points and the two arc centers (the original a, b positions).
        pts = {
            "ap": (ax + ox, ay + oy), "am": (ax - ox, ay - oy),
            "bp": (bx + ox, by + oy), "bm": (bx - ox, by - oy),
            "ca": (ax, ay), "cb": (bx, by),
        }
        result = [{"id": f"{sid}/{name}", "type": "point", "at": [x, y]}
                  for name, (x, y) in pts.items()]
        result.append({"id": f"{sid}/top", "type": "line",
                       "p1": f"{sid}/ap", "p2": f"{sid}/bp"})
        result.append({"id": f"{sid}/bottom", "type": "line",
                       "p1": f"{sid}/am", "p2": f"{sid}/bm"})
        result.append({"id": f"{sid}/cap_b", "type": "arc", "center": f"{sid}/cb",
                       "start": f"{sid}/bm", "end": f"{sid}/bp"})
        result.append({"id": f"{sid}/cap_a", "type": "arc", "center": f"{sid}/ca",
                       "start": f"{sid}/ap", "end": f"{sid}/am"})
        return result


def _seed_of(by_id: dict, point_id: str) -> tuple[float, float]:
    """The ``at`` seed of a referenced point entity (defaults to origin)."""
    entity = by_id.get(point_id, {})
    at = entity.get("at", [0.0, 0.0])
    return float(at[0]), float(at[1])


def _unit_perpendicular(ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """A unit vector perpendicular to a->b (defaults to +Y for a degenerate axis)."""
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return 0.0, 1.0
    return -dy / length, dx / length
