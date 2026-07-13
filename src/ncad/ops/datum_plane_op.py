"""The ``datum_plane`` feature op: a referenceable construction plane (a non-solid feature).

Distinct from a sketch (which produces a face profile): a datum plane is reference geometry
that later features name via ``datums.<id>`` (a sketch plane, a revolve axis via a datum
axis, patterns/mirrors). The working solid passes through unchanged (the builder treats
datum_plane as a non-solid op, like sketch).
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.datum_plane_params import DatumPlaneParamError, datum_plane_kwargs
from ncad.ops.op_result import OpResult


class DatumPlaneOp:
    """Builds a referenceable construction plane from a datum method."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Build the datum plane; its shape is reference geometry, not a new solid."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        try:
            kwargs = datum_plane_kwargs(params, refs)
        except DatumPlaneParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            plane = kernel.datum_plane(kwargs["method"], kwargs, refs)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=plane, provenance={}, issues=[])
