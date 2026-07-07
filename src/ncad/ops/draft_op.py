"""The ``draft`` feature op: taper selected faces about a neutral plane."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.draft_params import DraftParamError, draft_kwargs
from ncad.ops.op_result import OpResult


class DraftOp:
    """Tapers the incoming solid's selected faces by an angle about a neutral plane."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Draft the resolved ``faces`` of ``shape_in`` by ``angle`` about ``neutral``."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="draft has no solid")])
        faces = params.get("__refs__", {}).get("faces") or []
        if not faces:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="draft: no faces to taper")])
        try:
            kwargs = draft_kwargs(params)
        except DraftParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            result = kernel.draft(shape_in, faces, angle=kwargs["angle"],
                                  neutral=kwargs["neutral"],
                                  neutral_offset=kwargs["neutral_offset"])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
