"""Apply sketch-modify transforms (move/rotate/scale/mirror/pattern) before solving.

Runs after EntityExpander, so it sees only primitive point/line/arc/circle entities.
Each transform is an affine map of point ``at`` seeds (and, for scale, curve radii)
computed via AffineTransform. move/rotate/scale replace their sources in place;
mirror/pattern keep the sources and append fixed copies. Every emitted entity carries
``fixed: True`` so the solver treats transformed geometry as a rigid image. An empty or
absent transform list is a no-op. Contract violations raise TransformError.
"""

import logging

from ncad.sketch.affine_transform import AffineTransform
from ncad.sketch.id_padding import PaddedNaming

logger = logging.getLogger(__name__)

_CURVE_POINT_KEYS = {"line": ("p1", "p2"), "arc": ("center", "start", "end"),
                     "circle": ("center",)}


class TransformError(Exception):
    """A transform references unknown/empty sources or has invalid parameters."""


class TransformApplier:
    """Applies feature-level sketch transforms to expanded primitive entities."""

    def apply(self, entities: list[dict], transforms: list[dict]) -> list[dict]:
        """Return ``entities`` with each transform in ``transforms`` applied in order."""
        if not transforms:
            return entities
        current = list(entities)
        for transform in transforms:
            current = self._apply_one(current, transform)
        return current

    def _apply_one(self, entities: list[dict], transform: dict) -> list[dict]:
        """Apply a single transform, dispatching on its ``op``."""
        op = transform.get("op")
        handler_name = _TRANSFORM_HANDLERS.get(op) if isinstance(op, str) else None
        if handler_name is None:
            raise TransformError(f"unknown transform op {op!r}")
        by_id = {e["id"]: e for e in entities if "id" in e}
        source_ids = _resolve_sources(transform, by_id)
        return globals()[handler_name](transform, entities, source_ids, by_id)


def _resolve_sources(transform: dict, by_id: dict) -> list[str]:
    """Expand a transform's ``sources`` (each id, or a parent id to its children)."""
    raw = transform.get("sources") or []
    resolved: list[str] = []
    for sid in raw:
        if sid in by_id:
            resolved.append(sid)
            continue
        children = sorted(k for k in by_id if k.startswith(f"{sid}/"))
        if not children:
            raise TransformError(
                f"transform {transform.get('op')!r} references unknown source {sid!r}")
        resolved.extend(children)
    if not resolved:
        raise TransformError(f"transform {transform.get('op')!r} has no sources")
    return resolved


def _center_of(transform: dict, by_id: dict, key: str) -> tuple[float, float]:
    """A center as an explicit ``[x, y]`` or a referenced point id."""
    value = transform.get(key)
    if value is None:
        raise TransformError(f"transform {transform.get('op')!r} needs a {key!r}")
    if isinstance(value, str):
        point = by_id.get(value)
        if point is None or point.get("type") != "point":
            raise TransformError(f"{key!r} {value!r} is not a known point")
        return float(point["at"][0]), float(point["at"][1])
    return float(value[0]), float(value[1])


def _point_ids(source_ids: list[str], by_id: dict) -> list[str]:
    """Ordered unique point ids in the sources: explicit points + curve endpoints."""
    ordered: list[str] = []
    for sid in source_ids:
        source = by_id[sid]
        if source["type"] == "point":
            candidates = [sid]
        else:
            candidates = [source[key] for key in _CURVE_POINT_KEYS[source["type"]]]
        for pid in candidates:
            if pid not in ordered:
                ordered.append(pid)
    return ordered


def _curve_copies(source_ids: list[str], by_id: dict, affine: AffineTransform,
                  relabel: dict[str, str]) -> list[dict]:
    """Fixed copies of the source curves, re-pointed at their relabeled endpoints."""
    copies: list[dict] = []
    for sid in source_ids:
        source = by_id[sid]
        stype = source["type"]
        if stype == "point":
            continue
        copy: dict = {"id": relabel[sid], "type": stype, "fixed": True}
        for key in _CURVE_POINT_KEYS[stype]:
            copy[key] = relabel[source[key]]
        if stype in ("circle", "arc") and "radius" in source:
            copy["radius"] = float(source["radius"]) * affine.radius_factor
        copies.append(copy)
    return copies


def _replace_in_place(entities: list[dict], source_ids: list[str], by_id: dict,
                      affine: AffineTransform) -> list[dict]:
    """Re-emit the sources transformed under their own ids, keeping others as-is."""
    relabel = {sid: sid for sid in source_ids}
    point_ids = _point_ids(source_ids, by_id)
    for pid in point_ids:
        relabel.setdefault(pid, pid)
    transformed: dict[str, dict] = {}
    for pid in point_ids:
        x, y = affine.apply_point(float(by_id[pid]["at"][0]), float(by_id[pid]["at"][1]))
        transformed[pid] = {"id": pid, "type": "point", "at": [x, y], "fixed": True}
    for copy in _curve_copies(source_ids, by_id, affine, relabel):
        transformed[copy["id"]] = copy
    return [transformed.get(e.get("id"), e) if e.get("id") in transformed else e
            for e in entities]


def _append_copy(prefix: str, source_ids: list[str], by_id: dict,
                 affine: AffineTransform) -> list[dict]:
    """One namespaced copy of the sources, welding transform-invariant points.

    A point whose image coincides with its own original position (e.g. a point on a
    mirror axis) keeps its original id, so the copy stays connected to the source chain
    into a single loop. Other points get a ``prefix``-namespaced id.
    """
    point_ids = _point_ids(source_ids, by_id)
    relabel = {sid: f"{prefix}/{sid}" for sid in source_ids}
    emitted: list[dict] = []
    for pid in point_ids:
        ox, oy = float(by_id[pid]["at"][0]), float(by_id[pid]["at"][1])
        nx, ny = affine.apply_point(ox, oy)
        if abs(nx - ox) < 1e-9 and abs(ny - oy) < 1e-9:
            relabel[pid] = pid  # invariant point: weld to the original
            continue
        relabel[pid] = f"{prefix}/{pid}"
        emitted.append({"id": relabel[pid], "type": "point", "at": [nx, ny],
                        "fixed": True})
    emitted.extend(_curve_copies(source_ids, by_id, affine, relabel))
    return emitted


def _t_move(transform: dict, entities: list[dict], source_ids: list[str],
            by_id: dict) -> list[dict]:
    """Translate the sources in place by (dx, dy)."""
    affine = AffineTransform.translation(
        float(transform.get("dx", 0.0)), float(transform.get("dy", 0.0)))
    return _replace_in_place(entities, source_ids, by_id, affine)


def _t_rotate(transform: dict, entities: list[dict], source_ids: list[str],
              by_id: dict) -> list[dict]:
    """Rotate the sources in place about ``center`` by ``angle`` degrees CCW."""
    cx, cy = _center_of(transform, by_id, "center")
    affine = AffineTransform.rotation(cx, cy, float(transform.get("angle", 0.0)))
    return _replace_in_place(entities, source_ids, by_id, affine)


def _t_scale(transform: dict, entities: list[dict], source_ids: list[str],
             by_id: dict) -> list[dict]:
    """Uniformly scale the sources in place about ``center`` by ``factor``."""
    factor = float(transform.get("factor", 1.0))
    if factor == 0.0:
        raise TransformError("scale factor must be non-zero")
    cx, cy = _center_of(transform, by_id, "center")
    affine = AffineTransform.scaling(cx, cy, factor)
    return _replace_in_place(entities, source_ids, by_id, affine)


def _t_mirror(transform: dict, entities: list[dict], source_ids: list[str],
              by_id: dict) -> list[dict]:
    """Reflect the sources across ``axis`` and append the copies (sources kept)."""
    transform_id = _require_id(transform)
    axis = transform.get("axis")
    if not axis:
        raise TransformError("mirror transform needs an 'axis'")
    ax, ay = _axis_point(axis, by_id, "p1", 0)
    bx, by = _axis_point(axis, by_id, "p2", 1)
    if abs(ax - bx) < 1e-12 and abs(ay - by) < 1e-12:
        raise TransformError("mirror axis endpoints are coincident")
    affine = AffineTransform.reflection(ax, ay, bx, by)
    return _append_copies(transform_id, entities, source_ids, by_id, [affine])


def _t_pattern(transform: dict, entities: list[dict], source_ids: list[str],
               by_id: dict) -> list[dict]:
    """Replicate the sources ``count`` times (linear or circular); append copies."""
    transform_id = _require_id(transform)
    count = int(transform.get("count", 0))
    if count < 1:
        raise TransformError("pattern count must be >= 1")
    kind = transform.get("kind")
    if kind == "linear":
        dx, dy = float(transform.get("dx", 0.0)), float(transform.get("dy", 0.0))
        affines = [AffineTransform.translation(dx * i, dy * i) for i in range(1, count)]
    elif kind == "circular":
        cx, cy = _center_of(transform, by_id, "center")
        affines = [AffineTransform.rotation(cx, cy, _circular_step(transform, count) * i)
                   for i in range(1, count)]
    else:
        raise TransformError(f"unknown pattern kind {kind!r}")
    return _append_copies(transform_id, entities, source_ids, by_id, affines)


def _circular_step(transform: dict, count: int) -> float:
    """Degrees between adjacent circular-pattern copies.

    A full sweep (>= 360) spaces ``count`` copies evenly around the circle; a partial
    sweep spreads ``count`` copies across the arc (endpoints inclusive).
    """
    sweep = float(transform.get("angle", 360.0))
    if abs(sweep) >= 360.0 - 1e-9:
        return sweep / count
    return sweep / (count - 1) if count > 1 else 0.0


def _append_copies(transform_id: str, entities: list[dict], source_ids: list[str],
                   by_id: dict, affines: list[AffineTransform]) -> list[dict]:
    """Keep ``entities`` and append one namespaced copy of the sources per affine."""
    out = list(entities)
    copy_prefixes = PaddedNaming().child_ids(transform_id, len(affines))
    for prefix, affine in zip(copy_prefixes, affines):
        out.extend(_append_copy(prefix, source_ids, by_id, affine))
    return out


def _require_id(transform: dict) -> str:
    """The transform's ``id`` (required so copies get a namespace)."""
    tid = transform.get("id")
    if not tid:
        raise TransformError(f"{transform.get('op')!r} transform needs an 'id'")
    return tid


def _axis_point(axis: dict, by_id: dict, key: str, index: int) -> tuple[float, float]:
    """An axis endpoint from ``{p1,p2}`` point ids or a two-point ``[[x,y],[x,y]]``."""
    if isinstance(axis, dict):
        ref = axis.get(key)
        point = by_id.get(ref)
        if point is None or point.get("type") != "point":
            raise TransformError(f"mirror axis {key!r} {ref!r} is not a known point")
        return float(point["at"][0]), float(point["at"][1])
    endpoint = axis[index]
    return float(endpoint[0]), float(endpoint[1])


_TRANSFORM_HANDLERS = {
    "move": "_t_move",
    "rotate": "_t_rotate",
    "scale": "_t_scale",
    "mirror": "_t_mirror",
    "pattern": "_t_pattern",
}
