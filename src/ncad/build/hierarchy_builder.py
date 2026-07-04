"""Turn a resolved part dict into a display hierarchy for the viewer's tree tab.

A pure projection of the feature tree: part >> features (in authored order) >> a
sketch's elements. Carries only what the tree renders (id, op/kind, label); no
geometry, no kernel. The viewer fetches this as a ``<model>.hierarchy.json`` sidecar
and renders it Blender-style. Non-interactive: it describes structure, nothing more.
"""

import logging

logger = logging.getLogger(__name__)


class HierarchyBuilder:
    """Projects a part's feature tree into a nested display hierarchy."""

    def hierarchy(self, part_name: str, part: dict) -> dict:
        """Return the display tree for ``part`` named ``part_name``."""
        return {
            "name": part_name,
            "kind": "part",
            "op": part.get("profile", "part"),
            "children": [self._feature_node(f) for f in part.get("features", [])],
        }

    def _feature_node(self, feature: dict) -> dict:
        """One feature node, nesting a sketch's elements as children."""
        return {
            "id": feature.get("id", "?"),
            "kind": "feature",
            "op": feature.get("op", "?"),
            "children": [self._element_node(e) for e in feature.get("elements", [])],
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
