"""The per-part feature executor: walk features, thread the shape and element map.

Pure: same part dict yields identical geometry and the same element map (design
sections 0, 4). Before dispatching a feature, the Builder resolves the op's declared
reference fields (semantic / generative / selector) against the element map of the
current working solid, injecting resolved handles under the reserved ``__refs__`` key.
After dispatch it rebuilds the element map from the op's output so later features can
reference this feature's geometry. Unresolvable references are reported by feature id
and the feature is skipped; the build continues.
"""

import logging
from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.ops.build_issue import BuildIssue
from ncad.ops.edge_selector import EdgeSelector
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult
from ncad.refs.element_map import ElementMap
from ncad.refs.generative_tagger import GenerativeTagger
from ncad.refs.reference import Reference
from ncad.refs.reference_resolver import ReferenceResolver

logger = logging.getLogger(__name__)

# Which fields of each op name a reference, and what the resolved value should be:
#   "input" -> a shape used as the op's input (extrude's profile)
#   "shape" -> a prior feature's shape handle (pocket/boolean)
#   "face"  -> a resolved face Element (hole placement)
#   "edges" -> a list of edge handles (fillet/chamfer)
_REF_FIELDS: dict[str, dict[str, str]] = {
    "extrude": {"profile": "input"},
    "pocket": {"profile": "shape", "target": "shape"},
    "boolean": {"target": "shape", "tool": "shape"},
    "hole": {"on": "face"},
    "fillet": {"edges": "edges"},
    "chamfer": {"edges": "edges"},
}
_EDGE_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")
# Ops whose output is not a model solid (a sketch produces an input face); the element
# map tracks the working solid, so these do not rebuild it.
_NON_SOLID_OPS = frozenset({"sketch"})


class Builder:
    """Builds a single part's feature tree into a geometry handle and element map."""

    def __init__(self, kernel: Kernel, registry: OpRegistry) -> None:
        self._kernel = kernel
        self._registry = registry
        self._tagger = GenerativeTagger()

    def build_part(self, part: dict) -> OpResult:
        """Execute ``part["features"]`` in order and return the final result."""
        result, _ = self.build_part_mapped(part)
        return result

    def build_part_mapped(self, part: dict) -> tuple[OpResult, ElementMap]:
        """Like build_part, but also return the final ElementMap (for the sidecar)."""
        shape_by_id: dict[str, Any] = {}
        issues: list[BuildIssue] = []
        element_map = ElementMap()
        resolver = ReferenceResolver(element_map)
        previous_shape: Any = None

        for feature in part["features"]:
            feature_id = feature["id"]
            refs, shape_in = self._resolve_refs(
                feature, shape_by_id, previous_shape, element_map, resolver, issues)
            feature_with_refs = dict(feature)
            feature_with_refs["__refs__"] = refs
            builder_fn = self._registry.get(feature["op"])
            result = builder_fn(shape_in, feature_with_refs, {}, self._kernel)
            issues.extend(result.issues)
            shape_by_id[feature_id] = result.shape
            previous_shape = result.shape
            self._rebuild_map(element_map, feature, result.shape)

        return OpResult(shape=previous_shape, provenance={}, issues=issues), element_map

    def _resolve_refs(self, feature: dict, shape_by_id: dict, previous_shape: Any,
                      element_map: ElementMap, resolver: ReferenceResolver,
                      issues: list[BuildIssue]) -> tuple[dict, Any]:
        """Resolve the op's declared reference fields; return (__refs__, input shape)."""
        op = feature.get("op", "")
        feature_id = feature["id"]
        refs: dict[str, Any] = {}
        shape_in = previous_shape
        for field, role in _REF_FIELDS.get(op, {}).items():
            if field not in feature:
                continue
            value = feature[field]
            if role == "edges" and value in _EDGE_KEYWORDS:
                refs[field] = self._resolve_keyword_edges(previous_shape, value)
                continue
            resolution = resolver.resolve(
                Reference.parse(str(value)), shape_by_id, element_map.elements())
            if resolution.error is not None:
                issues.append(BuildIssue(node_id=feature_id, message=resolution.error))
                refs[field] = None
                continue
            refs[field] = _resolved_value(role, resolution)
            if role == "input":
                shape_in = refs[field]
        return refs, shape_in

    def _resolve_keyword_edges(self, shape_in: Any, keyword: str) -> list:
        """Keyword sugar: resolve one of the five edge keywords to edge handles."""
        if shape_in is None:
            return []
        return EdgeSelector().select(self._kernel.edges_of(shape_in), keyword)

    def _rebuild_map(self, element_map: ElementMap, feature: dict, shape: Any) -> None:
        """Rebuild the element map from a feature's output shape (faces first)."""
        if shape is None or feature.get("op", "") in _NON_SOLID_OPS:
            return
        descriptors = self._kernel.describe_elements(shape)
        faces = [d for d in descriptors if d["kind"] == "face"]
        tags = self._tagger.tags_for(feature.get("op", ""), feature.get("plane", "XY"), faces)
        element_map.rebuild(feature["id"], descriptors, tags)


def _resolved_value(role: str, resolution: Any) -> Any:
    """Convert a Resolution into the value an op expects for a field role."""
    if role == "edges":
        return [e.handle for e in resolution.elements]
    if role == "face":
        return resolution.elements[0] if resolution.elements else None
    return resolution.shapes[0] if resolution.shapes else None
