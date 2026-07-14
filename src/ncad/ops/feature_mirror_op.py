"""The ``feature_mirror`` op: re-apply a tool feature's cut/boss reflected across a plane.

The NX/Creo/Fusion "mirror feature": it references a tool-producing feature (its output solid
is the cutter or boss), reflects that tool across a plane (a base plane, {point, normal}, or a
planar face), and applies ONE boolean (cut or union) to the running solid. Distinct from the
3.x body ``mirror`` (which reflects the running body itself).
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.feature_mirror_params import FeatureMirrorParamError, feature_mirror_kwargs
from ncad.ops.op_result import OpResult


class FeatureMirrorOp:
    """Reflects a referenced tool feature's solid across a plane and applies one boolean."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="feature_mirror has no solid")])
        refs = dict(params.get("__refs__", {}))
        tool = refs.get("tool")
        if tool is None:
            return OpResult(shape=None, provenance={}, issues=[BuildIssue(
                node_id=feature_id, message="feature_mirror 'tool' feature did not resolve")])
        # A `face` ref resolves to an element descriptor; the plane parser needs the handle.
        if refs.get("face") is not None and hasattr(refs["face"], "handle"):
            refs["face"] = refs["face"].handle
        try:
            kwargs = feature_mirror_kwargs(params, refs)
        except FeatureMirrorParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            reflected = kernel.mirror(tool, plane=kwargs["plane"])
            if kwargs["operation"] == "cut":
                result = kernel.cut(shape_in, [reflected])
            else:
                result = kernel.fuse([shape_in, reflected])
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
