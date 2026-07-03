"""The per-build element/provenance map (design section 2).

Rebuilt after every feature from the kernel's descriptors of that feature's output
shape. Element ids are deterministic and namespaced by producing feature + role +
index (no randomness, so ids are stable across rebuilds and safe as reference names).
Provenance is carried forward by geometric matching: a face that survives a cut keeps
its origin feature; new topology belongs to the current feature. Cross-boolean
content-hash naming is the Phase 4 hardening, out of scope here.
"""

import logging
import math

from ncad.refs.element import Element

logger = logging.getLogger(__name__)


class ElementMap:
    """Holds the current build's elements with id/feature/tag/instance lookup."""

    def __init__(self) -> None:
        self._elements: list[Element] = []

    def rebuild(self, feature_id: str, descriptors: list[dict], tags: dict[int, str]) -> None:
        """Recompute the map from ``feature_id``'s output ``descriptors``.

        :param tags: descriptor-index -> generative tag (from GenerativeTagger).
        """
        previous = list(self._elements)
        prior_by_key = {_geometric_key(e.attrs, e.kind): e for e in previous}
        indexed = _assign_indices(feature_id, descriptors, tags)
        rebuilt: list[Element] = []
        for descriptor, element_id, _role, tag in indexed:
            attrs = _attrs_from(descriptor, feature_id, tag)
            key = _geometric_key(attrs, descriptor["kind"])
            match = prior_by_key.get(key)
            if match is not None:
                attrs["created_by"] = match.created_by
                rebuilt.append(Element(match.id, descriptor["kind"], match.created_by,
                                       match.tag, attrs, descriptor["handle"]))
            else:
                rebuilt.append(Element(element_id, descriptor["kind"], feature_id, tag,
                                       attrs, descriptor["handle"]))
        self._elements = rebuilt

    def elements(self) -> list[Element]:
        """All current elements."""
        return list(self._elements)

    def by_id(self, element_id: str) -> Element | None:
        """The element with ``element_id``, or None."""
        for element in self._elements:
            if element.id == element_id:
                return element
        return None

    def by_feature(self, feature_id: str) -> list[Element]:
        """Elements whose ``created_by`` is ``feature_id``."""
        return [e for e in self._elements if e.created_by == feature_id]

    def by_tag(self, tag: str) -> list[Element]:
        """Elements carrying generative ``tag``."""
        return [e for e in self._elements if e.tag == tag]

    def instance(self, feature_id: str, index: int) -> Element | None:
        """The ``index``-th element created by ``feature_id`` in canonical order."""
        members = self.by_feature(feature_id)
        ordered = sorted(members, key=lambda e: _canonical_sort_key(e.attrs, e.kind))
        return ordered[index] if 0 <= index < len(ordered) else None

    def to_sidecar(self) -> list[dict]:
        """Ordered records for the glTF element-map sidecar (mesh-part order)."""
        return [
            {"index": i, "id": e.id, "kind": e.kind,
             "created_by": e.created_by, "tag": e.tag}
            for i, e in enumerate(self._elements)
        ]


def _assign_indices(feature_id: str, descriptors: list[dict],
                    tags: dict[int, str]) -> list[tuple]:
    """Return (descriptor, id, role, tag) tuples with deterministic per-role indices."""
    by_role: dict[str, list[tuple]] = {}
    for i, descriptor in enumerate(descriptors):
        tag = tags.get(i)
        role = tag if tag is not None else descriptor["kind"]
        by_role.setdefault(role, []).append((descriptor, tag))
    result: list[tuple] = []
    for role, group in by_role.items():
        ordered = sorted(group, key=lambda t: _canonical_sort_key(
            t[0], t[0]["kind"], order=t[0].get("order")))
        for index, (descriptor, tag) in enumerate(ordered):
            result.append((descriptor, f"{feature_id}/{role}/{index}", role, tag))
    return result


def _canonical_sort_key(source: dict, kind: str, order: float | None = None) -> tuple:
    """Sort key: authored order first (if any), then centroid x,y,z, then size."""
    center = source.get("center") or (0.0, 0.0, 0.0)
    size = _size_of(source)
    ordinal = order if order is not None else math.inf
    return (ordinal, center[0], center[1], center[2], size)


def _geometric_key(attrs: dict, kind: str) -> tuple:
    """Rounded geometric identity for provenance carry-forward matching."""
    center = attrs.get("center") or (0.0, 0.0, 0.0)
    size = _size_of(attrs)
    return (kind, round(float(center[0]), 4), round(float(center[1]), 4),
            round(float(center[2]), 4), round(size, 4))


def _size_of(source: dict) -> float:
    """The scalar size of an element: face area, edge length, else 0."""
    raw = source.get("area")
    if raw is None:
        raw = source.get("length")
    return float(raw) if raw is not None else 0.0


def _attrs_from(descriptor: dict, feature_id: str, tag: str | None) -> dict:
    """Flatten a kernel descriptor into the queryable attribute dict."""
    attrs = dict(descriptor)
    attrs.pop("handle", None)
    attrs["created_by"] = feature_id
    attrs["tag"] = tag
    attrs["type"] = descriptor.get("geom_type")
    normal = descriptor.get("normal")
    if normal is not None:
        attrs["normal_x"], attrs["normal_y"], attrs["normal_z"] = normal
    return attrs
