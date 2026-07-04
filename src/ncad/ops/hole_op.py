"""The ``hole`` feature op: drill cylinders at explicit positions and subtract them."""

from typing import Any

from ncad.kernel.kernel import Kernel
from ncad.kernel.kernel_op_error import KernelOpError
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult

_PLANE_AXIS = {"XY": "Z", "XZ": "Y", "YZ": "X"}
_AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


class HoleOp:
    """Subtracts cylindrical holes at explicit positions from the incoming solid."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict[str, str],
              kernel: Kernel) -> OpResult:
        feature_id = params["id"]
        if shape_in is None:
            issue = BuildIssue(node_id=feature_id, message="hole has no solid to drill")
            return OpResult(shape=None, provenance={}, issues=[issue])
        on_face = params.get("__refs__", {}).get("on")
        if on_face is not None:
            axis, origin_on_axis = _axis_and_origin(on_face)
        else:
            axis = _PLANE_AXIS[params.get("plane", "XY")]
            origin_on_axis = 0.0
        diameter = params["diameter"]
        length = self._depth(params, shape_in, kernel)
        try:
            tools = [kernel.cylinder(_center(x, y, axis, origin_on_axis), axis, diameter, length)
                     for x, y in params["positions"]]
            result = kernel.cut(shape_in, tools)
        except KernelOpError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        return OpResult(shape=result, provenance={}, issues=[])

    @staticmethod
    def _depth(params: dict, solid: Any, kernel: Kernel) -> float:
        """Blind ``depth`` if given, else the solid's full z-extent for a through hole."""
        if not params.get("through"):
            return params["depth"]
        (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
        return maxz - minz


def _axis_and_origin(face: Any) -> tuple[str, float]:
    """Drill axis (dominant face-normal axis) and the face's coordinate on that axis."""
    normal = (face.attrs.get("normal_x", 0.0), face.attrs.get("normal_y", 0.0),
              face.attrs.get("normal_z", 1.0))
    axis = "XYZ"[max(range(3), key=lambda i: abs(normal[i]))]
    if axis == "Z":
        origin = face.attrs.get("max_z", 0.0)
    else:
        origin = face.attrs.get("center", (0.0, 0.0, 0.0))[_AXIS_INDEX[axis]]
    return axis, origin


def _center(x: float, y: float, axis: str, origin_on_axis: float) -> tuple:
    """Cylinder base center for a hole at (x, y) drilled along ``axis``."""
    if axis == "Z":
        return (x, y, origin_on_axis)
    if axis == "Y":
        return (x, origin_on_axis, y)
    return (origin_on_axis, x, y)
