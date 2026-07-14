"""The ``revolve`` feature op: revolve an upstream profile face about an axis into a solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.revolve_params import RevolveParamError, revolve_kwargs


class RevolveOp:
    """Revolves an upstream face about an axis into a solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Revolve the upstream profile face about the feature's ``axis``."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance=dict(provenance_in), issues=[BuildIssue(
                node_id=feature_id,
                message="revolve has no input face; its referenced profile did not build")])
        try:
            kwargs = revolve_kwargs(params, params.get("__refs__", {}))
        except RevolveParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            solid = kernel.revolve(shape_in, **kwargs)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=solid, provenance={}, issues=[],
                        history=kernel.history([shape_in], solid))
