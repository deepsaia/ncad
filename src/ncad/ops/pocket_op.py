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
        """Cut ``profile`` (a sketch) out of ``target`` (a solid).

        Both arrive as resolved shapes in ``__refs__`` (semantic feature references
        resolved by the Builder); if ``target`` is omitted, the incoming ``shape_in``
        (previous solid) is cut.
        """
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        target = refs.get("target") or shape_in
        if target is None:
            issue = BuildIssue(node_id=feature_id, message="pocket has no solid to cut")
            return OpResult(shape=None, provenance={}, issues=[issue])
        profile_face = refs.get("profile")
        if profile_face is None:
            issue = BuildIssue(node_id=feature_id, message="pocket profile did not resolve")
            return OpResult(shape=None, provenance={}, issues=[issue])
        try:
            tool = kernel.extrude(profile_face, params["distance"])
            result = kernel.cut(target, [tool])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
