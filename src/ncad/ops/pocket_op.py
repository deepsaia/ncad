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

        Both are named prior features resolved from ``__shapes__``; if ``target`` is
        omitted, the incoming ``shape_in`` (previous solid) is cut. (Interim reference
        scheme; bucket 0.3 replaces the named lookups with the real reference model.)
        """
        feature_id = params["id"]
        provenance = dict(provenance_in)
        shapes = params.get("__shapes__", {})
        target = shapes.get(params["target"]) if params.get("target") else shape_in
        if target is None:
            issue = BuildIssue(node_id=feature_id, message="pocket has no solid to cut")
            return OpResult(shape=None, provenance=provenance, issues=[issue])
        profile_face = shapes.get(params.get("profile"))
        if profile_face is None:
            issue = BuildIssue(node_id=feature_id,
                               message=f"pocket profile {params.get('profile')!r} not found")
            return OpResult(shape=None, provenance=provenance, issues=[issue])
        try:
            tool = kernel.extrude(profile_face, params["distance"])
            result = kernel.cut(target, [tool])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance=provenance,
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        provenance[feature_id] = "pocket"
        return OpResult(shape=result, provenance=provenance, issues=[])
