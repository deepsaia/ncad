"""The ``rib`` feature op: thicken an open profile into a blade and fuse it to a solid."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.rib_params import RibParamError, rib_kwargs


class RibOp:
    """Thickens an open profile wire into a blade and unions it into the target solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Build the rib blade from ``profile`` and fuse it into ``target`` (a solid)."""
        feature_id = params["id"]
        refs = params.get("__refs__", {})
        target = refs.get("target") or shape_in
        if target is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="rib has no solid to stiffen")])
        # A single profile, or a list of profiles for a web (multi-blade) rib fused in one op.
        profiles = refs.get("profiles") or ([refs["profile"]] if refs.get("profile") else [])
        if not profiles:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="rib profile did not resolve")])
        try:
            kwargs = rib_kwargs(params, refs)
        except RibParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        # An until-material rib grows to the target (auto-trimmed); a fixed rib grows by depth.
        to = target if kwargs["until"] else None
        try:
            result = target
            for profile in profiles:
                blade = kernel.rib(profile, thickness=kwargs["thickness"],
                                   depth=kwargs["depth"], to=to, side=kwargs["side"],
                                   draft=kwargs["draft"])
                result = kernel.fuse([result, blade])
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])
