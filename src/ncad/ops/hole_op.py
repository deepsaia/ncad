"""The ``hole`` feature op: drill cylinders at explicit positions and subtract them."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult

_PLANE_AXIS = {"XY": "Z", "XZ": "Y", "YZ": "X"}


class HoleOp:
    """Subtracts cylindrical holes at explicit positions from the incoming solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        provenance = dict(provenance_in)
        if shape_in is None:
            issue = BuildIssue(node_id=feature_id, message="hole has no solid to drill")
            return OpResult(shape=None, provenance=provenance, issues=[issue])
        plane = params.get("plane", "XY")
        axis = _PLANE_AXIS[plane]
        diameter = params["diameter"]
        length = self._depth(params, shape_in, kernel)
        try:
            tools = [kernel.cylinder((x, y, 0.0), axis, diameter, length)
                     for x, y in params["positions"]]
            result = kernel.cut(shape_in, tools)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance=provenance,
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        provenance[feature_id] = "hole"
        return OpResult(shape=result, provenance=provenance, issues=[])

    @staticmethod
    def _depth(params: dict, solid: Any, kernel: Kernel) -> float:
        """Blind ``depth`` if given, else the solid's full z-extent for a through hole."""
        if not params.get("through"):
            return params["depth"]
        (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
        return maxz - minz
