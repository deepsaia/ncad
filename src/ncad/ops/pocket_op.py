"""The ``pocket`` feature op: extrude a profile and subtract it from the current solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.extrude_params import ExtrudeParamError, extrude_kwargs
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
            kwargs = extrude_kwargs(params, refs)
        except ExtrudeParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        # A through/to-next pocket extrudes the tool up to the solid being cut, so the cut
        # target doubles as the extrude target when the end-condition uses `until`.
        if kwargs.get("until") is not None and "target" not in kwargs:
            kwargs["target"] = target
        try:
            tool = kernel.extrude(profile_face, **kwargs)
            result = kernel.cut(target, [tool])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
