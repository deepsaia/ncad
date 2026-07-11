"""Turn a resolved part dict into a display hierarchy for the viewer's tree tab.

A projection of the feature tree: part >> features (in authored order) >> a sketch's
elements, plus a trailing **Bodies** group listing each built body with its resolved
material. Carries only what the tree renders (id, op/kind, label, a sketch's constraint
status inline, and per-body material chips); no geometry. Material is a per-body property
(NX/Fusion model), so it shows in the Bodies group, not on feature/part rows. The viewer
fetches this as a ``<model>.hierarchy.json`` sidecar and renders it Blender-style.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HierarchyBuilder:
    """Projects a part's feature tree (plus a Bodies group) into a nested display hierarchy."""

    def hierarchy(self, part_name: str, part: dict, statuses: Any = None,
                  bodies: Any = None) -> dict:
        """Return the display tree for ``part`` named ``part_name``.

        :param statuses: optional list of SketchStatus; each is stamped onto its sketch
            feature node so the tree shows constraint status inline (bucket 1.5 surfaced it in
            a separate box; the tree now owns it).
        :param bodies: optional list of ``{"id", "material"}`` dicts (one per built body, with
            the material resolved per body); rendered as a trailing Bodies group. Material is a
            per-body property, so it lives here, not on feature/part rows.
        """
        by_feature = {s.feature_id: s for s in (statuses or [])}
        children = [self._feature_node(f, by_feature) for f in part.get("features", [])]
        node = {
            "name": part_name,
            "kind": "part",
            "op": part.get("profile", "part"),
            "children": children,
        }
        # A single contiguous body IS the part, so no Bodies group: if that one body has a
        # material, it rides as a chip on the part row (part == body). A Bodies group only
        # appears for a genuinely MULTIBODY part, where it disambiguates which solid is which
        # material. Materials are optional and never auto-defaulted, so a plain single-solid
        # part with no material shows just the clean feature tree.
        body_list = bodies or []
        if len(body_list) > 1:
            children.append(self._bodies_group(body_list))
        elif len(body_list) == 1 and body_list[0].get("material"):
            node["material"] = body_list[0]["material"]
        return node

    def _feature_node(self, feature: dict, by_feature: dict) -> dict:
        """One feature node, nesting a sketch's elements and carrying status inline."""
        node = {
            "id": feature.get("id", "?"),
            "kind": "feature",
            "op": feature.get("op", "?"),
            "children": [self._element_node(e) for e in feature.get("elements", [])],
        }
        status = by_feature.get(feature.get("id"))
        if status is not None:
            # Inline sketch constraint status: the dot/dof/failing render on this row itself.
            node["status"] = status.status
            node["dof"] = status.dof
            node["failing_ids"] = list(status.failing_ids)
        return node

    @staticmethod
    def _bodies_group(bodies: list) -> dict:
        """The trailing Bodies group: one node per built body with its resolved material."""
        return {
            "name": "Bodies",
            "kind": "group",
            "op": f"{len(bodies)}",
            "children": [
                {"id": b["id"], "kind": "body", "op": "",
                 "material": b.get("material"), "children": []}
                for b in bodies
            ],
        }

    @staticmethod
    def _element_node(element: dict) -> dict:
        """One sketch-element leaf node."""
        return {
            "id": element.get("id", "?"),
            "kind": "element",
            "op": element.get("type", "?"),
            "children": [],
        }
