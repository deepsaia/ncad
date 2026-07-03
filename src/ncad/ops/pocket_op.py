"""The ``pocket`` feature op: extrude a profile and subtract it from the current solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


class PocketOp:
    """Cuts an extruded profile out of the incoming solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """:param shape_in: The solid to cut (the previous feature's shape)."""
        feature_id = params["id"]
        provenance = dict(provenance_in)
        if shape_in is None:
            issue = BuildIssue(node_id=feature_id, message="pocket has no solid to cut")
            return OpResult(shape=None, provenance=provenance, issues=[issue])
        profile_face = params.get("__shapes__", {}).get(params.get("profile"))
        if profile_face is None:
            issue = BuildIssue(node_id=feature_id,
                               message=f"pocket profile {params.get('profile')!r} not found")
            return OpResult(shape=None, provenance=provenance, issues=[issue])
        try:
            tool = kernel.extrude(profile_face, params["distance"])
            result = kernel.cut(shape_in, [tool])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance=provenance,
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        provenance[feature_id] = "pocket"
        return OpResult(shape=result, provenance=provenance, issues=[])
