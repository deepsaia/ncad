"""The ``path3d`` leaf op: a free 3D wire (a sweep path), no upstream shape.

A no-input reference-geometry feature (like a datum): it ignores ``shape_in`` and mints an open 3D
wire through the authored points, which a later ``sweep`` names as its ``path``. This is what lets a
sweep follow a centerline that turns in all three axes (a planar open sketch cannot). The wire is
not a model solid; the builder tracks it like a sketch face, not the working solid.
"""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.path3d_params import Path3dParamError, path3d_kwargs


class Path3dOp:
    """Builds an open 3D wire (a sweep path) from ordered [x, y, z] points."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        """Build the 3D path wire from its ``points`` + ``kind`` (polyline/spline)."""
        node_id = params.get("id", "path3d")
        try:
            kwargs = path3d_kwargs(params)
        except Path3dParamError as exc:
            return OpResult(shape=None, issues=[BuildIssue(node_id=node_id, message=str(exc))])
        try:
            wire = kernel.wire3d(kwargs["points"], kind=kwargs["kind"], closed=kwargs["closed"])
        except KernelOpError as exc:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id=node_id, message=f"path3d {kwargs['kind']!r} failed: {exc}")])
        return OpResult(shape=wire, provenance={}, issues=[])
