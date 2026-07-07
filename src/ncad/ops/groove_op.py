"""The ``groove`` feature op: revolve a tool profile and cut it from the current solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.revolve_params import RevolveParamError, revolve_kwargs


class GrooveOp:
    """Revolves a profile into a tool and cuts it out of the incoming solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Revolve ``profile`` about ``axis`` and cut it from ``target`` (a solid)."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        target = refs.get("target") or shape_in
        if target is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="groove has no solid to cut")])
        profile_face = refs.get("profile")
        if profile_face is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="groove profile did not resolve")])
        try:
            kwargs = revolve_kwargs(params, refs)
        except RevolveParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            tool = kernel.revolve(profile_face, **kwargs)
            result = kernel.cut(target, [tool])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
