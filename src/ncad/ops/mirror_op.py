"""The ``mirror`` feature op: reflect the running body/bodies across a plane."""

from typing import Any

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
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
                # keep + no merge: originals keep their ids/materials; the reflections are NEW
                # geometry, so they are re-minted under this feature (fresh ids) rather than
                # colliding with the originals' ids. For a single-body input this is just
                # <id>/body/0 (original) + <id>/body/1 (reflection); for a multibody input the
                # originals pass through and each reflected body is born here.
                result_shape = self._keep_separate(shape_in, reflected, feature_id, kernel)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result_shape, provenance={}, issues=[])

    @staticmethod
    def _keep_separate(original: Any, reflected: Any, feature_id: str,
                       kernel: Kernel) -> BodySet:
        """Original + reflected bodies, all born under ``feature_id`` with unique ids.

        The reflected set carries the originals' ids (kernel.mirror preserves them), which would
        collide with the originals. Both sets are new geometry for this symmetric result, so all
        bodies are minted here with a running index (``<feature_id>/body/<n>``), each keeping its
        source body's created_by (so a reflected steel body stays steel) - preserving per-body
        material while guaranteeing unique addressable ids.
        """
        bodies = [*kernel.bodies(original), *kernel.bodies(reflected)]
        minted = [Body(id=f"{feature_id}/body/{i}", kind=b.kind, shape=b.shape,
                       created_by=b.created_by)
                  for i, b in enumerate(bodies)]
        return BodySet(minted)
