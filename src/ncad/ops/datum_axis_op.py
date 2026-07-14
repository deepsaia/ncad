"""The ``datum_axis`` feature op: a referenceable construction axis (a non-solid feature).

Reference geometry that later features name via ``datums.<id>`` (a revolve axis, a circular
pattern axis, a datum plane through an axis). The working solid passes through unchanged.
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.datum_axis_params import DatumAxisParamError, datum_axis_kwargs
from ncad.ops.op_result import OpResult


class DatumAxisOp:
    """Builds a referenceable construction axis from a datum method."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Build the datum axis; its shape is an ``(point, dir)`` reference tuple."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        try:
            kwargs = datum_axis_kwargs(params, refs)
        except DatumAxisParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            axis = kernel.datum_axis(kwargs["method"], kwargs, refs)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=axis, provenance={}, issues=[])
