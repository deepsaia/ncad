"""The ``transform`` feature op: move/rotate/scale a body, in place or as a copy."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.transform_params import TransformParamError, transform_kwargs


class TransformOp:
    """Moves/rotates/scales the incoming body; copy=true adds a new body."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Transform ``shape_in`` (in place) or add a transformed copy as a new body."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="transform has no solid")])
        try:
            kwargs = transform_kwargs(params)
        except TransformParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            moved = kernel.transform(shape_in, move=kwargs["move"], rotate=kwargs["rotate"],
                                     scale=kwargs["scale"])
            if kwargs["copy"]:
                # copy=true keeps the original AND adds the transformed body: the 3.0
                # keep-separate producer mints a new born id for each, preserving identity.
                result_shape = kernel.union_bodies([shape_in, moved], origin=feature_id)
            else:
                result_shape = moved
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result_shape, provenance={}, issues=[])
