"""The ``loft`` feature op: blend a solid through ordered section profiles."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.loft_params import LoftParamError, loft_kwargs
from ncad.ops.op_result import OpResult


class LoftOp:
    """Lofts a solid through an ordered list of referenced section profiles."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Blend a solid through the resolved ``sections`` (plus optional point caps)."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        sections = refs.get("sections", [])
        try:
            kwargs = loft_kwargs(params, refs)
        except LoftParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            solid = kernel.loft(list(sections), ruled=kwargs["ruled"],
                                start_point=kwargs["start_point"],
                                end_point=kwargs["end_point"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=solid, provenance={}, issues=[])
