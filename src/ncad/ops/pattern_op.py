"""The ``pattern`` feature op: replicate the running body/bodies in a linear/circular array."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.pattern_params import PatternParamError, pattern_kwargs
from ncad.ops.pattern_placements import PatternPlacements


class PatternOp:
    """Replicates ``shape_in`` at each computed placement, fused or kept separate."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Pattern the running body/bodies; merge=true fuses, false keeps N bodies."""
        feature_id = params["id"]
        if shape_in is None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id,
                                               message="pattern has no solid")])
        try:
            kwargs = pattern_kwargs(params)
        except PatternParamError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            specs = PatternPlacements(
                kwargs, anchor=self._anchor(kwargs, shape_in, kernel)).specs()
            # Per-instance suppress drops the named born-once ordinals BEFORE union. Note:
            # union_bodies numbers body/0..N by list position, so suppressing an INTERIOR
            # ordinal renumbers later bodies under this producer (a suppress-stable id map is a
            # follow-up); suppressing END ordinals leaves the rest stable, the common case (a
            # bolt circle missing a couple of clocking holes).
            suppress = set(kwargs.get("suppress", []))
            specs = [spec for k, spec in enumerate(specs) if k not in suppress]
            # Seed (ordinal 0) is the untouched source; copies apply their transform. This
            # keeps instance 0 geometrically exact and defines the stable generation order.
            copies = [shape_in if not spec else kernel.transform(shape_in, **spec)
                      for spec in specs]
            if kwargs["merge"]:
                # merge=true fuses to one body (a fillable star, a merged array).
                result_shape = kernel.fuse(copies) if len(copies) > 1 else copies[0]
            else:
                # Keep-separate: born-once ordinal body ids pattern_id/body/k (k = generation
                # ordinal, NOT a geometric sort), the stable instance identity that closes R2.
                result_shape = kernel.union_bodies(copies, origin=feature_id)
        except (KernelOpError, ValueError) as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result_shape, provenance={}, issues=[])

    @staticmethod
    def _anchor(kwargs: dict, shape_in: Any, kernel: Kernel
                ) -> tuple[float, float, float] | None:
        """Bounding-box center, needed only for circular rotate=false placement."""
        if kwargs["kind"] != "circular" or kwargs["circular"]["rotate"]:
            return None
        (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(shape_in)
        return ((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0)
