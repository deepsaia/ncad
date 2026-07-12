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

from ncad.build.cache_key import CacheKeyBuilder
from ncad.build.feature_cache import CacheEntry, FeatureCache
from ncad.build.rebuild_graph import RebuildGraph
from ncad.kernel.kernel import Kernel
from ncad.ops.build_issue import BuildIssue
from ncad.ops.edge_selector import EdgeSelector
from ncad.ops.face_selector import FaceSelector
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult
from ncad.ops.sketch_status import SketchStatus
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
    "extrude": {"profile": "input", "to": "face"},
    "pocket": {"profile": "shape", "target": "shape", "to": "face"},
    "boolean": {"target": "shape", "tool": "shape", "tools": "shape_list"},
    "revolve": {"profile": "input"},
    "groove": {"profile": "shape", "target": "shape"},
    "sweep": {"profile": "input", "path": "shape", "sections": "shape_list",
              "guides": "shape_list"},
    "loft": {"sections": "shape_list"},
    "rib": {"profile": "shape", "target": "shape"},
    "shell": {"openings": "face_list"},
    "draft": {"faces": "face_list"},
    "wrap": {"on": "face", "profile": "shape"},
    "hole": {"on": "face"},
    "fillet": {"edges": "edges"},
    "chamfer": {"edges": "edges"},
    "sketch": {"project": "edges"},
    "defeature": {"face": "face"},
    # offset ignores the face today (whole-solid); declaring it future-proofs per-face offset.
    "offset": {"face": "face"},
    "move_face": {"face": "face"},
    "relate": {"reference": "face", "moving": "face"},
}
_EDGE_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")
_FACE_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")
# Ops whose output is not a model solid (a sketch produces an input face); the element
# map tracks the working solid, so these do not rebuild it.
_NON_SOLID_OPS = frozenset({"sketch"})


class Builder:
    """Builds a single part's feature tree into a geometry handle and element map."""

    def __init__(self, kernel: Kernel, registry: OpRegistry,
                 cache: FeatureCache | None = None) -> None:
        self._kernel = kernel
        self._registry = registry
        self._tagger = GenerativeTagger()
        self._cache = cache

    def build_part(self, part: dict) -> OpResult:
        """Execute ``part["features"]`` in order and return the final result."""
        result, _, _ = self.build_part_mapped(part)
        return result

    def build_part_mapped(
        self, part: dict
    ) -> tuple[OpResult, ElementMap, list[SketchStatus]]:
        """Like build_part, but also return the final ElementMap (for the sidecar).

        When a FeatureCache is present, features are walked in the RebuildGraph's
        topological order and keyed by a chained content hash; a cache hit restores the
        shape + element descriptors without running the op, so only the dirty suffix of
        a parameter edit re-executes.
        """
        features = part["features"]
        by_id = {f["id"]: f for f in features}
        graph = RebuildGraph(features)
        order = graph.order()
        key_builder = CacheKeyBuilder(self._kernel.version()) if self._cache else None
        keys: dict[str, str] = {}

        shape_by_id: dict[str, Any] = {}
        issues: list[BuildIssue] = []
        statuses: list[SketchStatus] = []
        element_map = ElementMap()
        resolver = ReferenceResolver(element_map)
        previous_shape: Any = None
        last_id: str | None = None
        failed: set[str] = set()

        for feature_id in order:
            feature = by_id[feature_id]

            # Skip-and-suppress: a feature that depends on a failed one fails with a
            # single "depends on failed" issue rather than running and emitting its own
            # spurious geometry errors.
            failed_dep = next((d for d in graph.deps(feature_id) if d in failed), None)
            if failed_dep is not None:
                issues.append(BuildIssue(
                    node_id=feature_id,
                    message=f"depends on failed feature {failed_dep}"))
                self._mark_failed(feature_id, failed, shape_by_id)
                previous_shape = None
                last_id = feature_id
                continue

            refs, shape_in, ref_error = self._resolve_refs(
                feature, shape_by_id, previous_shape, element_map, resolver)
            if ref_error is not None:
                issues.append(BuildIssue(node_id=feature_id, message=ref_error))
                self._mark_failed(feature_id, failed, shape_by_id)
                previous_shape = None
                last_id = feature_id
                continue

            entry = None
            if self._cache is not None and key_builder is not None:
                dep_keys = [keys[d] for d in graph.deps(feature_id) if d in keys]
                keys[feature_id] = key_builder.key(feature, dep_keys)
                entry = self._cache.get(keys[feature_id])
            if entry is not None and self._cache is not None:
                self._cache.record(feature_id, hit=True)
                result = OpResult(shape=entry.shape, provenance={}, issues=[],
                                  status_report=entry.status_report)
                self._rebuild_map_from_descriptors(element_map, feature, entry.descriptors)
                # Restore the persistent names assigned on the first build so a cache hit keeps
                # identical element identity (names are not re-derived from lineage on a hit).
                if entry.names is not None:
                    element_map.apply_names(entry.names)
            else:
                # A feature's `scope` (merge scope: which bodies it targets/produces) rides
                # in the feature dict to the op. In bucket 3.0 it defaults to all bodies and
                # no op dispatches per-body yet; it is reserved for per-body dispatch in 3.4.
                feature_with_refs = dict(feature)
                feature_with_refs["__refs__"] = refs
                builder_fn = self._registry.get(feature["op"])
                result = builder_fn(shape_in, feature_with_refs, {}, self._kernel)
                issues.extend(result.issues)
                descriptors = self._rebuild_map(element_map, feature, result.shape,
                                                result.history)
                errors = [i for i in result.issues if i.level == "error"]
                succeeded = result.shape is not None and not errors
                if not succeeded:
                    failed.add(feature_id)
                # Only a successful feature is cached, so a failure re-runs and
                # re-reports on the next build (issues are never swallowed by a hit).
                if self._cache is not None and feature_id in keys:
                    self._cache.record(feature_id, hit=False)
                    if succeeded:
                        self._cache.put(keys[feature_id], CacheEntry(
                            result.shape, descriptors, result.status_report,
                            names=[e.id for e in element_map.elements()]))
            if result.status_report is not None:
                statuses.append(result.status_report)
            shape_by_id[feature_id] = result.shape
            # The running solid an implicit-input op (pattern/transform/mirror/wrap/...) inherits
            # is the last SOLID-producing feature, not the last feature: a sketch produces a face,
            # not a body, so it must not become `previous_shape` (mirrors the dependency graph's
            # `previous_solid`, which skips _NON_SOLID_OPS). Otherwise an op that runs right after
            # a sketch would grab the face as its base solid.
            if feature.get("op", "") not in _NON_SOLID_OPS:
                previous_shape = result.shape
            last_id = feature_id

        final_shape = shape_by_id.get(last_id) if last_id is not None else None
        return (OpResult(shape=final_shape, provenance={}, issues=issues),
                element_map, statuses)

    def _mark_failed(self, feature_id: str, failed: set[str],
                     shape_by_id: dict[str, Any]) -> None:
        """Record a feature as failed with no output shape (skip-and-suppress)."""
        failed.add(feature_id)
        shape_by_id[feature_id] = None
        if self._cache is not None:
            self._cache.record(feature_id, hit=False)

    def _resolve_refs(self, feature: dict, shape_by_id: dict, previous_shape: Any,
                      element_map: ElementMap,
                      resolver: ReferenceResolver) -> tuple[dict, Any, str | None]:
        """Resolve the op's declared reference fields.

        Returns ``(refs, shape_in, error)`` where ``error`` is the first reference
        resolution failure message, or None. The caller skips the op and marks the
        feature failed when ``error`` is not None (skip-and-suppress), so one broken
        reference yields one primary issue rather than a cascade.
        """
        op = feature.get("op", "")
        refs: dict[str, Any] = {}
        shape_in = previous_shape
        for field, role in _REF_FIELDS.get(op, {}).items():
            if field not in feature:
                continue
            value = feature[field]
            # A list-valued field resolves each reference: `shape_list` (sweep sections/
            # guides) to a list of shape handles; otherwise (e.g. a sketch's ``project``)
            # to concatenated edge handles.
            if isinstance(value, list):
                if role == "shape_list":
                    shapes, error = self._resolve_shape_list(
                        value, shape_by_id, element_map, resolver)
                elif role == "face_list":
                    shapes, error = self._resolve_face_list(
                        value, shape_by_id, element_map, resolver)
                else:
                    shapes, error = self._resolve_edge_list(
                        value, shape_by_id, element_map, resolver)
                if error is not None:
                    return refs, shape_in, error
                refs[field] = shapes
                continue
            if role == "edges" and value in _EDGE_KEYWORDS:
                refs[field] = self._resolve_keyword_edges(previous_shape, value)
                continue
            if role == "face_list" and value in _FACE_KEYWORDS:
                refs[field] = self._resolve_keyword_faces(previous_shape, value)
                continue
            resolution = resolver.resolve(
                Reference.parse(str(value)), shape_by_id, element_map.elements())
            if resolution.error is not None:
                return refs, shape_in, resolution.error
            refs[field] = _resolved_value(role, resolution)
            if role == "input":
                shape_in = refs[field]
        return refs, shape_in, None

    def _resolve_edge_list(self, references: list, shape_by_id: dict,
                           element_map: ElementMap,
                           resolver: ReferenceResolver) -> tuple[list, str | None]:
        """Resolve a list of references to a concatenated list of edge handles."""
        handles: list = []
        for reference in references:
            resolution = resolver.resolve(
                Reference.parse(str(reference)), shape_by_id, element_map.elements())
            if resolution.error is not None:
                return handles, resolution.error
            handles.extend(e.handle for e in resolution.elements)
        return handles, None

    def _resolve_shape_list(self, references: list, shape_by_id: dict,
                            element_map: ElementMap,
                            resolver: ReferenceResolver) -> tuple[list, str | None]:
        """Resolve a list of references each to its shape handle (sweep sections/guides)."""
        shapes: list = []
        for reference in references:
            resolution = resolver.resolve(
                Reference.parse(str(reference)), shape_by_id, element_map.elements())
            if resolution.error is not None:
                return shapes, resolution.error
            shapes.append(resolution.shapes[0] if resolution.shapes else None)
        return shapes, None

    def _resolve_keyword_edges(self, shape_in: Any, keyword: str) -> list:
        """Keyword sugar: resolve one of the five edge keywords to edge handles."""
        if shape_in is None:
            return []
        return EdgeSelector().select(self._kernel.edges_of(shape_in), keyword)

    def _resolve_keyword_faces(self, shape_in: Any, keyword: str) -> list:
        """Keyword sugar: resolve a face keyword to face handles via describe_elements."""
        if shape_in is None:
            return []
        faces = [d for d in self._kernel.describe_elements(shape_in) if d["kind"] == "face"]
        return FaceSelector().select(faces, keyword)

    def _resolve_face_list(self, references: list, shape_by_id: dict,
                           element_map: ElementMap,
                           resolver: ReferenceResolver) -> tuple[list, str | None]:
        """Resolve a list of references to a concatenated list of face handles."""
        handles: list = []
        for reference in references:
            resolution = resolver.resolve(
                Reference.parse(str(reference)), shape_by_id, element_map.elements())
            if resolution.error is not None:
                return handles, resolution.error
            handles.extend(e.handle for e in resolution.elements)
        return handles, None

    def _rebuild_map(self, element_map: ElementMap, feature: dict, shape: Any,
                     history: Any = None) -> list | None:
        """Rebuild the element map from a feature's output shape; return descriptors."""
        if shape is None or feature.get("op", "") in _NON_SOLID_OPS:
            return None
        descriptors = self._kernel.describe_elements(shape)
        self._apply_descriptors(element_map, feature, descriptors, history)
        return descriptors

    def _rebuild_map_from_descriptors(self, element_map: ElementMap, feature: dict,
                                      descriptors: list | None) -> None:
        """Rebuild the element map from cached descriptors (no kernel call).

        No history is threaded on the cache-hit path; the caller restores the cached persistent
        names via ``element_map.apply_names`` right after this, so lineage is not re-derived.
        """
        if descriptors is None:
            return
        self._apply_descriptors(element_map, feature, descriptors)

    def _apply_descriptors(self, element_map: ElementMap, feature: dict,
                           descriptors: list, history: Any = None) -> None:
        """Tag faces and rebuild the map from descriptors (shared hit/miss path)."""
        faces = [d for d in descriptors if d["kind"] == "face"]
        tags = self._tagger.tags_for(feature.get("op", ""), feature.get("plane", "XY"), faces)
        element_map.rebuild(feature["id"], descriptors, tags, history)


def _resolved_value(role: str, resolution: Any) -> Any:
    """Convert a Resolution into the value an op expects for a field role."""
    if role == "edges":
        return [e.handle for e in resolution.elements]
    if role == "face":
        return resolution.elements[0] if resolution.elements else None
    return resolution.shapes[0] if resolution.shapes else None
