"""The ``primitive`` leaf op: a base solid (box/cylinder/sphere/cone/torus/wedge), no sketch.

A no-input base-body feature (like ``import``): it ignores ``shape_in`` and mints a primitive
solid a part may start from or a later boolean may consume. Distinct from a sketched extrude.
"""

import logging
from typing import Any

from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.primitive_params import PrimitiveParamError, primitive_kwargs

logger = logging.getLogger(__name__)


class PrimitiveOp:
    """Builds a primitive base solid from its kind + dimensions."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "primitive")
        try:
            kwargs = primitive_kwargs(params)
        except PrimitiveParamError as exc:
            return OpResult(shape=None, issues=[BuildIssue(node_id=node_id, message=str(exc))])
        try:
            shape = kernel.make_primitive(
                kwargs["kind"], kwargs["dims"], kwargs["plane"], kwargs["at"],
                kwargs["plane_offset"])
        except KernelOpError as exc:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id=node_id, message=f"primitive {kwargs['kind']!r} failed: {exc}")])
        return OpResult(shape=shape)
