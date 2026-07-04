"""The ``boolean`` feature op: combine two prior features (cut / union / intersect)."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


class BooleanOp:
    """Combines two referenced prior feature solids via cut, union, or intersect."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        target = refs.get("target")
        tool = refs.get("tool")
        if target is None or tool is None:
            return OpResult(shape=None, provenance={}, issues=[BuildIssue(
                node_id=feature_id, message="boolean needs resolved target and tool")])
        operation = params.get("operation", "cut")
        try:
            result = self._apply(kernel, operation, target, tool)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])

    @staticmethod
    def _apply(kernel: Kernel, operation: str, target: Any, tool: Any) -> Any:
        """Dispatch to the kernel boolean for ``operation``."""
        if operation == "cut":
            return kernel.cut(target, [tool])
        if operation == "union":
            return kernel.fuse([target, tool])
        if operation == "intersect":
            return kernel.intersect([target, tool])
        raise ValueError(f"unknown boolean operation {operation!r}")
