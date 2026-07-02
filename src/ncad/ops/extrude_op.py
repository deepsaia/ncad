"""The ``extrude`` feature op: turn a face into a solid by extruding its normal."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


class ExtrudeOp:
    """Extrudes an upstream face into a solid."""

    def build(
        self, shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel
    ) -> OpResult:
        """Extrude the upstream face by ``params["distance"]``.

        :param shape_in: The face produced by the referenced sketch feature.
        :param params: The feature dict (``id``, ``distance``).
        :param provenance_in: Provenance accumulated from earlier features.
        :param kernel: Geometry backend.
        :return: An :class:`OpResult` whose shape is the solid, or ``None`` + an issue.
        """
        feature_id = params["id"]
        if shape_in is None:
            issue = BuildIssue(
                node_id=feature_id,
                message="extrude has no input face; its referenced profile did not build",
            )
            return OpResult(shape=None, provenance=dict(provenance_in), issues=[issue])

        solid = kernel.extrude(shape_in, params["distance"])
        provenance = dict(provenance_in)
        provenance[feature_id] = "extrude"
        return OpResult(shape=solid, provenance=provenance, issues=[])
