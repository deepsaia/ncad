"""Apply sketch-modify topology ops (trim/extend/fillet/chamfer) before solving.

Runs after EntityExpander and before TransformApplier, so it sees primitive entities and
its output is what a subsequent mirror/pattern copies. Intersections are computed from
seed ``at`` coordinates via GeometryIntersector; the entity graph is rewritten (endpoints
moved, fillet arcs / chamfer lines inserted) and emitted as ``fixed: True`` primitives.
An empty or absent modify list is a no-op. Contract/geometry violations raise
TopologyError.
"""

import logging
import math

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
    """Return entities with ``line``'s ``end_key`` re-pointed at the trim/extend point.

    If ``hit`` coincides with an existing point (e.g. the tool line's own corner), that
    point's id is reused so the trimmed/extended edge welds to the shared vertex and the
    loop stays closed; otherwise a new fixed point ``new_id`` is minted.
    """
    welded = _coincident_point_id(entities, hit)
    endpoint_id = welded if welded is not None else new_id
    out: list[dict] = []
    for entity in entities:
        if entity["id"] == line["id"]:
            out.append({**entity, end_key: endpoint_id, "fixed": True})
        else:
            out.append(entity)
    if welded is None:
        out.append({"id": new_id, "type": "point", "at": [hit[0], hit[1]],
                    "fixed": True})
    return out


def _coincident_point_id(entities: list[dict], hit: tuple[float, float]) -> str | None:
    """The id of an existing point entity coincident with ``hit`` (within eps), or None."""
    for entity in entities:
        if entity.get("type") != "point":
            continue
        px, py = float(entity["at"][0]), float(entity["at"][1])
        if _dist_sq((px, py), hit) < 1e-12:
            return entity["id"]
    return None


def _m_fillet(op: dict, entities: list[dict]) -> list[dict]:
    """Round the corner at ``at`` (two lines) with a tangent arc of ``radius``."""
    radius = float(op.get("radius", 0.0))
    if radius <= 0.0:
        raise TopologyError(f"fillet at {op.get('at')!r} needs a positive radius")
    corner_id = op["at"]
    line_a, line_b = _corner_entities(corner_id, entities, op)
    seeds = _seeds(entities)
    corner = seeds[corner_id]
    ua = _line_dir(line_a, corner_id, seeds)
    ub = _line_dir(line_b, corner_id, seeds)
    center, ta, tb = _fillet_geometry(corner, ua, ub, radius, op)
    prefix = f"{corner_id}/fillet"
    new_points = [
        {"id": f"{prefix}/a", "type": "point", "at": [ta[0], ta[1]], "fixed": True},
        {"id": f"{prefix}/b", "type": "point", "at": [tb[0], tb[1]], "fixed": True},
        {"id": f"{prefix}/c", "type": "point", "at": [center[0], center[1]],
         "fixed": True},
    ]
    arc = _oriented_arc(f"{prefix}/arc", f"{prefix}/c", f"{prefix}/a", f"{prefix}/b",
                        center, ta, tb)
    rewired = _repoint_corner(entities, line_a, line_b, corner_id,
                              f"{prefix}/a", f"{prefix}/b")
    return rewired + new_points + [arc]


def _m_chamfer(op: dict, entities: list[dict]) -> list[dict]:
    """Bevel the corner at ``at`` (two lines) with a line set back by ``setback``."""
    setback = float(op.get("setback", 0.0))
    if setback <= 0.0:
        raise TopologyError(f"chamfer at {op.get('at')!r} needs a positive setback")
    corner_id = op["at"]
    line_a, line_b = _corner_entities(corner_id, entities, op)
    seeds = _seeds(entities)
    corner = seeds[corner_id]
    ua = _line_dir(line_a, corner_id, seeds)
    ub = _line_dir(line_b, corner_id, seeds)
    pa = (corner[0] + ua[0] * setback, corner[1] + ua[1] * setback)
    pb = (corner[0] + ub[0] * setback, corner[1] + ub[1] * setback)
    prefix = f"{corner_id}/chamfer"
    new_points = [
        {"id": f"{prefix}/a", "type": "point", "at": [pa[0], pa[1]], "fixed": True},
        {"id": f"{prefix}/b", "type": "point", "at": [pb[0], pb[1]], "fixed": True},
    ]
    seg = {"id": f"{prefix}/line", "type": "line", "p1": f"{prefix}/a",
           "p2": f"{prefix}/b", "fixed": True}
    rewired = _repoint_corner(entities, line_a, line_b, corner_id,
                              f"{prefix}/a", f"{prefix}/b")
    return rewired + new_points + [seg]


def _corner_entities(corner_id: str, entities: list[dict], op: dict) -> tuple[dict, dict]:
    """The exactly-two line entities sharing ``corner_id``; else a TopologyError."""
    touching = [e for e in entities
                if e.get("type") in ("line", "arc", "circle")
                and corner_id in _endpoint_ids(e)]
    if len(touching) != 2:
        raise TopologyError(f"corner {corner_id!r} must be shared by exactly two "
                            f"entities (found {len(touching)})")
    if any(e["type"] != "line" for e in touching):
        raise TopologyError(f"corner {corner_id!r}: fillet/chamfer supports line-line "
                            f"corners only in this bucket")
    return touching[0], touching[1]


def _endpoint_ids(entity: dict) -> tuple:
    """The connecting point ids of a line/arc (empty for a circle)."""
    if entity["type"] == "line":
        return entity["p1"], entity["p2"]
    if entity["type"] == "arc":
        return entity["start"], entity["end"]
    return ()


def _line_dir(line: dict, from_id: str, seeds: dict) -> tuple[float, float]:
    """Unit direction of ``line`` pointing AWAY from the corner point ``from_id``."""
    other = line["p2"] if line["p1"] == from_id else line["p1"]
    fx, fy = seeds[from_id]
    ox, oy = seeds[other]
    dx, dy = ox - fx, oy - fy
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise TopologyError(f"degenerate line {line['id']!r} at corner {from_id!r}")
    return dx / length, dy / length


def _fillet_geometry(corner: tuple, ua: tuple, ub: tuple, radius: float,
                     op: dict) -> tuple[tuple, tuple, tuple]:
    """Arc center + the two tangent points for a fillet between two rays from a corner.

    The center sits along the interior angle bisector at distance radius/sin(theta/2);
    each tangent point is the foot of the perpendicular from the center onto a ray.
    """
    dot = max(-1.0, min(1.0, ua[0] * ub[0] + ua[1] * ub[1]))
    theta = math.acos(dot)
    if theta < 1e-6 or abs(theta - math.pi) < 1e-6:
        raise TopologyError(f"fillet at {op.get('at')!r}: the two lines are collinear")
    tan_dist = radius / math.tan(theta / 2.0)
    ta = (corner[0] + ua[0] * tan_dist, corner[1] + ua[1] * tan_dist)
    tb = (corner[0] + ub[0] * tan_dist, corner[1] + ub[1] * tan_dist)
    bx, by = ua[0] + ub[0], ua[1] + ub[1]
    blen = math.hypot(bx, by)
    center_dist = radius / math.sin(theta / 2.0)
    center = (corner[0] + bx / blen * center_dist, corner[1] + by / blen * center_dist)
    return center, ta, tb


def _oriented_arc(arc_id: str, center_id: str, a_id: str, b_id: str,
                  center: tuple, ta: tuple, tb: tuple) -> dict:
    """A CCW arc from a to b; swap ends if a->b would sweep the wrong way.

    WireOrderer draws arcs CCW start->end about center. Choose start/end so the CCW span
    is the minor arc (the fillet), by checking the cross product of the two radial vecs.
    """
    ax, ay = ta[0] - center[0], ta[1] - center[1]
    bx, by = tb[0] - center[0], tb[1] - center[1]
    cross = ax * by - ay * bx
    if cross >= 0.0:
        return {"id": arc_id, "type": "arc", "center": center_id,
                "start": a_id, "end": b_id, "fixed": True}
    return {"id": arc_id, "type": "arc", "center": center_id,
            "start": b_id, "end": a_id, "fixed": True}


def _repoint_corner(entities: list[dict], line_a: dict, line_b: dict, corner_id: str,
                    a_id: str, b_id: str) -> list[dict]:
    """Re-point line_a's corner end to a_id and line_b's corner end to b_id (fixed)."""
    remap = {line_a["id"]: a_id, line_b["id"]: b_id}
    out: list[dict] = []
    for entity in entities:
        new_id = remap.get(entity["id"])
        if new_id is None:
            out.append(entity)
            continue
        end_key = "p1" if entity["p1"] == corner_id else "p2"
        out.append({**entity, end_key: new_id, "fixed": True})
    return out


def _m_split(op: dict, entities: list[dict]) -> list[dict]:
    """Cut ``of`` into two entities at the projection of ``at`` onto it."""
    by_id = {e["id"]: e for e in entities}
    seeds = _seeds(entities)
    entity = _require(by_id, op["of"], op)
    target = _target_xy(op["at"], seeds)
    cut = _project_onto(entity, target, by_id, seeds, op)
    cut_id = f"{op['id']}/x"
    cut_point = {"id": cut_id, "type": "point", "at": [cut[0], cut[1]], "fixed": True}
    if entity["type"] == "line":
        halves = [
            {"id": f"{op['id']}/0", "type": "line", "p1": entity["p1"], "p2": cut_id,
             "fixed": True},
            {"id": f"{op['id']}/1", "type": "line", "p1": cut_id, "p2": entity["p2"],
             "fixed": True},
        ]
    elif entity["type"] == "arc":
        halves = [
            {"id": f"{op['id']}/0", "type": "arc", "center": entity["center"],
             "start": entity["start"], "end": cut_id, "fixed": True},
            {"id": f"{op['id']}/1", "type": "arc", "center": entity["center"],
             "start": cut_id, "end": entity["end"], "fixed": True},
        ]
    else:
        raise TopologyError(f"cannot split a {entity['type']!r} (split {op.get('id')!r})")
    kept = [e for e in entities if e["id"] != entity["id"]]
    return kept + [cut_point] + halves


def _project_onto(entity: dict, target: tuple, by_id: dict, seeds: dict,
                  op: dict) -> tuple[float, float]:
    """Project ``target`` onto ``entity``; raise if the foot is outside its span."""
    if entity["type"] == "line":
        ax, ay = seeds[entity["p1"]]
        bx, by = seeds[entity["p2"]]
        dx, dy = bx - ax, by - ay
        seg_sq = dx * dx + dy * dy
        if seg_sq < 1e-12:
            raise TopologyError(f"split {op.get('id')!r}: zero-length target line")
        t = ((target[0] - ax) * dx + (target[1] - ay) * dy) / seg_sq
        if t <= 1e-9 or t >= 1.0 - 1e-9:
            raise TopologyError(f"split {op.get('id')!r}: point not on segment")
        return (ax + t * dx, ay + t * dy)
    if entity["type"] == "arc":
        cx, cy = seeds[entity["center"]]
        radius = _seed_radius_pt(entity, seeds)
        ang = math.atan2(target[1] - cy, target[0] - cx)
        point = (cx + radius * math.cos(ang), cy + radius * math.sin(ang))
        if not _arc_span_contains(entity, point, seeds):
            raise TopologyError(f"split {op.get('id')!r}: point not on arc")
        return point
    raise TopologyError(f"cannot split a {entity['type']!r} (split {op.get('id')!r})")


def _seed_radius_pt(curve: dict, seeds: dict) -> float:
    """An arc's radius from seed points (center to start)."""
    cx, cy = seeds[curve["center"]]
    sx, sy = seeds[curve["start"]]
    return math.hypot(sx - cx, sy - cy)


def _arc_span_contains(arc: dict, point: tuple, seeds: dict) -> bool:
    """Whether ``point`` lies within the arc's CCW span from start to end."""
    cx, cy = seeds[arc["center"]]
    sx, sy = seeds[arc["start"]]
    ex, ey = seeds[arc["end"]]
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    ap = math.atan2(point[1] - cy, point[0] - cx)
    span = (a1 - a0) % (2 * math.pi)
    rel = (ap - a0) % (2 * math.pi)
    return 1e-9 < rel < span - 1e-9


_MODIFY_HANDLERS = {
    "trim": "_m_trim",
    "extend": "_m_extend",
    "fillet": "_m_fillet",
    "chamfer": "_m_chamfer",
    "split": "_m_split",
}
