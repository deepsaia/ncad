"""Turn a resolved part dict into a display hierarchy for the viewer's tree tab.

A pure projection of the feature tree: part >> features (in authored order) >> a
sketch's elements. Carries only what the tree renders (id, op/kind, label, an optional
material chip, and a sketch's constraint status inline); no geometry, no kernel. The viewer
fetches this as a ``<model>.hierarchy.json`` sidecar and renders it Blender-style.
Non-interactive: it describes structure, nothing more.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HierarchyBuilder:
    """Projects a part's feature tree into a nested display hierarchy."""

    def hierarchy(self, part_name: str, part: dict, statuses: Any = None) -> dict:
        """Return the display tree for ``part`` named ``part_name``.

        :param statuses: optional list of SketchStatus; each is stamped onto its sketch
            feature node so the tree shows constraint status inline (bucket 1.5 surfaced it in
            a separate box; the tree now owns it).
        """
        by_feature = {s.feature_id: s for s in (statuses or [])}
        node = {
            "name": part_name,
            "kind": "part",
            "op": part.get("profile", "part"),
            "children": [self._feature_node(f, by_feature) for f in part.get("features", [])],
        }
        # The part's default material rides on the part node as a chip (a body inherits it
        # unless its feature overrides; see MaterialResolver).
        if "material" in part:
            node["material"] = part["material"]
        return node

    def _feature_node(self, feature: dict, by_feature: dict) -> dict:
        """One feature node, nesting a sketch's elements and carrying material/status inline."""
        node = {
            "id": feature.get("id", "?"),
            "kind": "feature",
            "op": feature.get("op", "?"),
            "children": [self._element_node(e) for e in feature.get("elements", [])],
        }
        if "material" in feature:
            node["material"] = feature["material"]
        status = by_feature.get(feature.get("id"))
        if status is not None:
            # Inline sketch constraint status: the dot/dof/failing render on this row itself.
            node["status"] = status.status
            node["dof"] = status.dof
            node["failing_ids"] = list(status.failing_ids)
        return node

    @staticmethod
    def _element_node(element: dict) -> dict:
        """One sketch-element leaf node."""
        return {
            "id": element.get("id", "?"),
            "kind": "element",
            "op": element.get("type", "?"),
            "children": [],
        }
