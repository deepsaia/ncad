"""The per-part feature executor: walk features in order, thread the shape.

Pure: same part dict yields identical geometry (design §0, §4). Randomness and
authoring live upstream. A feature's input shape is the shape of the feature named by
its ``profile`` field, if present, else the previous feature's shape. Provenance and
issues accumulate across the walk; a feature that references a missing profile is
reported by id rather than crashing the build.
"""

import logging
from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class Builder:
    """Builds a single part's feature tree into a geometry handle."""

    def __init__(self, kernel: Kernel, registry: OpRegistry) -> None:
        """:param kernel: Geometry backend. :param registry: Op-dispatch registry."""
        self._kernel = kernel
        self._registry = registry

    def build_part(self, part: dict) -> OpResult:
        """Execute ``part["features"]`` in order and return the final result.

        :param part: A part dict (``profile``, ``features``).
        :return: An :class:`OpResult` for the last feature, carrying merged provenance
            and all accumulated issues.
        """
        shape_by_id: dict[str, Any] = {}
        provenance: dict[str, str] = {}
        issues: list[BuildIssue] = []
        previous_shape: Any = None

        for feature in part["features"]:
            feature_id = feature["id"]
            shape_in = self._resolve_input(feature, shape_by_id, previous_shape, issues)
            builder_fn = self._registry.get(feature["op"])
            result = builder_fn(shape_in, feature, provenance, self._kernel)
            provenance = result.provenance
            issues.extend(result.issues)
            shape_by_id[feature_id] = result.shape
            previous_shape = result.shape

        return OpResult(shape=previous_shape, provenance=provenance, issues=issues)

    def _resolve_input(
        self,
        feature: dict,
        shape_by_id: dict[str, Any],
        previous_shape: Any,
        issues: list[BuildIssue],
    ) -> Any:
        """Input shape for ``feature``: its named ``profile``, else previous shape."""
        profile_ref = feature.get("profile")
        if profile_ref is None:
            return previous_shape
        if profile_ref not in shape_by_id:
            issues.append(
                BuildIssue(
                    node_id=feature["id"],
                    message=f"feature references profile {profile_ref!r} which does not exist",
                )
            )
            return None
        return shape_by_id[profile_ref]
