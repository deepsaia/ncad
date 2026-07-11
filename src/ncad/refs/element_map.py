"""The per-build element/provenance map (design section 2).

Rebuilt after every feature from the kernel's descriptors of that feature's output shape.
Element ids are TopoShape-style persistent names derived from construction lineage by the
PersistentNamer (bucket 4.1): a carried/modified element keeps its name across edits, fresh
topology gets a content hash folding its parents' names, and a history-free op (import, or a
backend that reports no history) seeds names from geometry. Names are deterministic (no
randomness), so they are stable across rebuilds and safe as reference names.
"""

import logging
import math

from ncad.kernel.element_history import ElementHistory
from ncad.refs.element import Element
from ncad.refs.persistent_namer import PersistentNamer, geometric_seed_name

logger = logging.getLogger(__name__)


class ElementMap:
    """Holds the current build's elements with id/feature/tag/instance lookup."""

    def __init__(self) -> None:
        self._elements: list[Element] = []
        self._namer = PersistentNamer()

    def rebuild(self, feature_id: str, descriptors: list[dict], tags: dict[int, str],
                history: ElementHistory | None = None) -> None:
        """Recompute the map from ``feature_id``'s output ``descriptors`` and lineage.

        With ``history`` (the hardened path), persistent names come from construction lineage
        (PersistentNamer): a carried/modified element keeps its identity and origin, fresh
        topology gets a content hash folding its parents' names. Without history (ops not yet
        instrumented, and the general case today), fall back to GEOMETRIC CARRY-FORWARD: an
        element whose geometry matches a prior element keeps that element's name and
        ``created_by`` (so provenance survives a later feature), and genuinely new geometry gets
        a fresh geometric-seed name owned by this feature. Both paths yield ``#kind/owner/hash``
        names and are deterministic.

        :param tags: descriptor-index -> generative tag (from GenerativeTagger).
        """
        if history is not None:
            self._rebuild_from_history(feature_id, descriptors, tags, history)
            return
        self._rebuild_from_geometry(feature_id, descriptors, tags)

    def _rebuild_from_history(self, feature_id: str, descriptors: list[dict],
                              tags: dict[int, str], history: ElementHistory) -> None:
        """Assign names from construction lineage (the hardened persistent-name path)."""
        prior_by_handle = {e.handle: e.id for e in self._elements}
        prior_owner = {e.id: e.created_by for e in self._elements}
        names = self._namer.name_elements(feature_id, feature_id, descriptors, tags,
                                          history, prior_by_handle)
        rebuilt: list[Element] = []
        for index, descriptor in enumerate(descriptors):
            name = names[index]
            tag = tags.get(index)
            attrs = _attrs_from(descriptor, feature_id, tag)
            # A carried/modified element inherits its prior owner; fresh topology is this feature.
            created_by = prior_owner.get(name, feature_id)
            attrs["created_by"] = created_by
            rebuilt.append(Element(name, descriptor["kind"], created_by, tag,
                                   attrs, descriptor["handle"]))
        self._elements = rebuilt

    def _rebuild_from_geometry(self, feature_id: str, descriptors: list[dict],
                               tags: dict[int, str]) -> None:
        """Carry names/provenance forward by geometric match; seed new geometry by this feature.

        This is the no-history fallback: it preserves the pre-4.1 behavior (a face that survives
        keeps its origin feature) while emitting persistent ``#kind/owner/hash`` names.
        """
        prior_by_key = {_geometric_key(e.attrs, e.kind): e for e in self._elements}
        rebuilt: list[Element] = []
        for index, descriptor in enumerate(descriptors):
            tag = tags.get(index)
            attrs = _attrs_from(descriptor, feature_id, tag)
            match = prior_by_key.get(_geometric_key(attrs, descriptor["kind"]))
            if match is not None:
                attrs["created_by"] = match.created_by
                rebuilt.append(Element(match.id, descriptor["kind"], match.created_by,
                                       match.tag, attrs, descriptor["handle"]))
            else:
                name = geometric_seed_name(descriptor["kind"], descriptor, feature_id)
                attrs["created_by"] = feature_id
                rebuilt.append(Element(name, descriptor["kind"], feature_id, tag,
                                       attrs, descriptor["handle"]))
        self._elements = rebuilt

    def apply_names(self, names: list[str]) -> None:
        """Overwrite element ids from a cached name list (positional), for cache-hit restore."""
        if len(names) != len(self._elements):
            logger.warning("cached name count %d != element count %d; keeping computed names",
                           len(names), len(self._elements))
            return
        for element, name in zip(self._elements, names):
            element.id = name

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
        """The ``index``-th instance created by ``feature_id``.

        When the feature's elements carry born-once body ids (``<feature>/body/<n>``, minted
        by a pattern), resolution is by that stable ordinal (n == index), NOT a geometric
        sort: suppressing one instance never renumbers the others (foundational-risk R2).
        A feature with no body-id ordinals is a single-body feature and keeps the legacy
        centroid-ordered behavior.
        """
        members = self.by_feature(feature_id)
        ordinals = _body_ordinals(members)
        if ordinals:
            for element in members:
                if ordinals.get(element.id) == index:
                    return element
            return None
        ordered = sorted(members, key=lambda e: _canonical_sort_key(e.attrs, e.kind))
        return ordered[index] if 0 <= index < len(ordered) else None

    def to_sidecar(self) -> list[dict]:
        """Ordered records for the glTF element-map sidecar (mesh-part order)."""
        return [
            {"index": i, "id": e.id, "kind": e.kind,
             "created_by": e.created_by, "tag": e.tag,
             # body_id lets the viewer group face-primitives by body (for material coloring).
             # Material itself is document data, stamped later by the builder, not here.
             "body_id": e.attrs.get("body_id")}
            for i, e in enumerate(self._elements)
        ]


def _canonical_sort_key(source: dict, kind: str, order: float | None = None) -> tuple:
    """Sort key: authored order first (if any), then centroid x,y,z, then size."""
    center = source.get("center") or (0.0, 0.0, 0.0)
    size = _size_of(source)
    ordinal = order if order is not None else math.inf
    return (ordinal, center[0], center[1], center[2], size)


def _geometric_key(attrs: dict, kind: str) -> tuple:
    """Rounded geometric identity for the no-history provenance carry-forward match."""
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


def _body_ordinals(members: list[Element]) -> dict[str, int]:
    """Map element id -> its body ordinal n for members whose body_id is ``.../body/<n>``.

    Empty when no member carries a parseable body-id ordinal (a single-body feature).
    """
    ordinals: dict[str, int] = {}
    for element in members:
        body_id = element.attrs.get("body_id")
        if not isinstance(body_id, str) or "/body/" not in body_id:
            continue
        suffix = body_id.rsplit("/body/", 1)[1]
        if suffix.isdigit():
            ordinals[element.id] = int(suffix)
    return ordinals


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
