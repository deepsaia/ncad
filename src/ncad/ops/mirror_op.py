"""The ``mirror`` feature op: reflect the running body/bodies across a plane."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.mirror_params import MirrorParamError, mirror_kwargs
from ncad.ops.op_result import OpResult


class MirrorOp:
    """Reflects ``shape_in`` across a plane; keeps the original by default (symmetry)."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Mirror the running body/bodies; combine per keep/merge."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="mirror has no solid")])
        try:
            kwargs = mirror_kwargs(params)
        except MirrorParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            reflected = kernel.mirror(shape_in, plane=kwargs["plane"])
            if not kwargs["keep"]:
                # keep=false reflects in place: only the reflected shape, no original.
                result_shape = reflected
            elif kwargs["merge"]:
                # keep + merge: one symmetric solid (fuse original with its reflection).
                result_shape = kernel.fuse([shape_in, reflected])
            else:
                # keep + no merge: 2 addressable bodies via the 3.0 born-once producer -
                # <id>/body/0 is the original, <id>/body/1 the reflection.
                result_shape = kernel.union_bodies([shape_in, reflected], origin=feature_id)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result_shape, provenance={}, issues=[])
