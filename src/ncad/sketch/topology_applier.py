"""Apply sketch-modify topology ops (trim/extend/fillet/chamfer) before solving.

Runs after EntityExpander and before TransformApplier, so it sees primitive entities and
its output is what a subsequent mirror/pattern copies. Intersections are computed from
seed ``at`` coordinates via GeometryIntersector; the entity graph is rewritten (endpoints
moved, fillet arcs / chamfer lines inserted) and emitted as ``fixed: True`` primitives.
An empty or absent modify list is a no-op. Contract/geometry violations raise
TopologyError.
"""

import logging

from ncad.sketch.geometry_intersector import GeometryIntersector

logger = logging.getLogger(__name__)

_INTERSECTOR = GeometryIntersector()


class TopologyError(Exception):
    """A topology op references unknown entities or has no valid intersection."""


class TopologyApplier:
    """Applies feature-level sketch topology ops to expanded primitive entities."""

    def apply(self, entities: list[dict], modify: list[dict]) -> list[dict]:
        """Return ``entities`` with each modify op applied in order."""
        if not modify:
            return entities
        current = list(entities)
        for op in modify:
            current = self._apply_one(current, op)
        return current

    def _apply_one(self, entities: list[dict], op: dict) -> list[dict]:
        """Apply a single modify op, dispatching on its ``op`` field."""
        name = op.get("op")
        handler = _MODIFY_HANDLERS.get(name) if isinstance(name, str) else None
        if handler is None:
            raise TopologyError(f"unknown modify op {name!r}")
        return globals()[handler](op, entities)


def _seeds(entities: list[dict]) -> dict[str, tuple[float, float]]:
    """Map every point entity id to its (x, y) seed."""
    return {e["id"]: (float(e["at"][0]), float(e["at"][1]))
            for e in entities if e.get("type") == "point"}


def _require(by_id: dict, eid: str, op: dict) -> dict:
    """Return entity ``eid`` or raise a TopologyError tagged with the op id."""
    entity = by_id.get(eid)
    if entity is None:
        raise TopologyError(f"{op.get('op')} {op.get('id')!r} references unknown "
                            f"entity {eid!r}")
    return entity


def _target_xy(ref, seeds: dict) -> tuple[float, float]:
    """A location as an explicit [x, y] or a referenced point id."""
    if isinstance(ref, str):
        if ref not in seeds:
            raise TopologyError(f"unknown point {ref!r}")
        return seeds[ref]
    return float(ref[0]), float(ref[1])


def _intersect_or_raise(a: dict, b: dict, seeds: dict, op: dict) -> list[tuple]:
    """Intersections of a and b, or a TopologyError if there are none."""
    hits = _INTERSECTOR.intersect(a, b, seeds)
    if not hits:
        raise TopologyError(f"{op.get('op')} {op.get('id')!r}: entities "
                            f"{op.get('of')!r} and {op.get('at') or op.get('to')!r} "
                            f"do not intersect")
    return hits


def _nearest(hits: list[tuple], target: tuple[float, float]) -> tuple[float, float]:
    """The hit point closest to ``target``."""
    return min(hits, key=lambda h: (h[0] - target[0]) ** 2 + (h[1] - target[1]) ** 2)


def _dist_sq(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Squared distance between two points."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _m_trim(op: dict, entities: list[dict]) -> list[dict]:
    """Cut ``of`` at its intersection with ``at``, keeping the ``keep`` side."""
    by_id = {e["id"]: e for e in entities}
    seeds = _seeds(entities)
    line = _require(by_id, op["of"], op)
    tool = _require(by_id, op["at"], op)
    keep_xy = _target_xy(op["keep"], seeds)
    hit = _nearest(_intersect_or_raise(line, tool, seeds, op), keep_xy)
    return _move_far_endpoint(entities, line, keep_xy, hit, f"{op['id']}/x")


def _m_extend(op: dict, entities: list[dict]) -> list[dict]:
    """Lengthen ``of`` so its nearest endpoint reaches its intersection with ``to``."""
    by_id = {e["id"]: e for e in entities}
    seeds = _seeds(entities)
    line = _require(by_id, op["of"], op)
    tool = _require(by_id, op["to"], op)
    hits = _intersect_or_raise(line, tool, seeds, op)
    best = min((("p1", _nearest(hits, seeds[line["p1"]])),
                ("p2", _nearest(hits, seeds[line["p2"]]))),
               key=lambda pair: _dist_sq(pair[1], seeds[line[pair[0]]]))
    end_key, hit = best
    return _set_endpoint(entities, line, end_key, hit, f"{op['id']}/x")


def _move_far_endpoint(entities: list[dict], line: dict, keep_xy: tuple,
                       hit: tuple, new_id: str) -> list[dict]:
    """Move the line endpoint FARTHER from ``keep_xy`` to ``hit`` (keep the near side)."""
    seeds = _seeds(entities)
    d1 = _dist_sq(seeds[line["p1"]], keep_xy)
    d2 = _dist_sq(seeds[line["p2"]], keep_xy)
    far_key = "p1" if d1 > d2 else "p2"
    return _set_endpoint(entities, line, far_key, hit, new_id)


def _set_endpoint(entities: list[dict], line: dict, end_key: str, hit: tuple,
                  new_id: str) -> list[dict]:
    """Return entities with ``line``'s ``end_key`` re-pointed at a new fixed point."""
    new_point = {"id": new_id, "type": "point", "at": [hit[0], hit[1]], "fixed": True}
    out: list[dict] = []
    for entity in entities:
        if entity["id"] == line["id"]:
            out.append({**entity, end_key: new_id, "fixed": True})
        else:
            out.append(entity)
    out.append(new_point)
    return out


_MODIFY_HANDLERS = {
    "trim": "_m_trim",
    "extend": "_m_extend",
}
