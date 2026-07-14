"""The ``split`` feature op: divide the running body by a plane into addressable bodies."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.split_params import SplitParamError, split_kwargs


class SplitOp:
    """Splits ``shape_in`` by a plane; keeps both halves (addressable) or one side."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Split the running body; keep=both -> 2 bodies, top/bottom -> one shape."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="split has no solid")])
        tool = params.get("__refs__", {}).get("tool")
        try:
            kwargs = split_kwargs(params, has_tool=tool is not None)
        except SplitParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            # Split by a TOOL BODY (region partition) if a tool is referenced, else by a plane.
            if tool is not None:
                parts = kernel.split_by_tool(shape_in, tool, keep=kwargs["keep"])
            else:
                parts = kernel.split(shape_in, plane=kwargs["plane"], keep=kwargs["keep"])
            if len(parts) == 1:
                result_shape = parts[0]           # keep=top/bottom: a single shape
            else:
                # keep=both: two addressable bodies via the born-once producer -
                # halves/body/0 (top) + halves/body/1 (bottom).
                result_shape = kernel.union_bodies(parts, origin=feature_id)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result_shape, provenance={}, issues=[])
