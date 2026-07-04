import pytest

from ncad.ops.hole_op import HoleOp
from ncad.ops.sketch_op import SketchOp
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _block(kernel, w=80, h=60, t=8):
    face = SketchOp().build(None, {"id": "sk", "op": "sketch", "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}, {}, kernel).shape
    return kernel.extrude(face, t)


def test_hole_drills_positions_through() -> None:
    import math

    kernel = FakeKernel()
    solid = _block(kernel)
    feature = {"id": "holes", "op": "hole", "plane": "XY", "diameter": 6.0, "through": True,
               "positions": [[10, 10], [70, 10], [10, 50], [70, 50]]}

    result = HoleOp().build(solid, feature, {}, kernel)

    assert result.issues == []
    removed = 4 * math.pi * 9.0 * 8.0  # 4 holes, r=3, depth=thickness 8 (through)
    assert kernel.volume(result.shape) == pytest.approx(80 * 60 * 8 - removed, rel=0.05)


def test_hole_without_solid_reports_issue() -> None:
    kernel = FakeKernel()
    feature = {"id": "holes", "op": "hole", "diameter": 6.0, "depth": 4.0, "positions": [[10, 10]]}

    result = HoleOp().build(None, feature, {}, kernel)

    assert result.shape is None
    assert result.issues[0].node_id == "holes"


def test_hole_on_face_ref_drills_along_face_normal() -> None:
    kernel = FakeKernel()
    solid = _block(kernel, w=40, h=40, t=10)
    cap = Element(id="pad/cap(+Z)/0", kind="face", created_by="pad", tag="cap(+Z)",
                  attrs={"center": (0.0, 0.0, 10.0), "normal_x": 0.0, "normal_y": 0.0,
                         "normal_z": 1.0, "max_z": 10.0, "min_z": 10.0},
                  handle=object())
    feature = {"id": "h", "op": "hole", "diameter": 4, "depth": 5,
               "positions": [[10, 10]], "on": "pad.cap(+Z)",
               "__refs__": {"on": cap}}
    made = []
    original_cylinder = kernel.cylinder

    def _spy_cylinder(center, axis, diameter, length):
        tool = original_cylinder(center, axis, diameter, length)
        made.append(tool)
        return tool

    kernel.cylinder = _spy_cylinder  # type: ignore[method-assign]
    result = HoleOp().build(solid, feature, {}, kernel)

    assert result.issues == [] and result.shape is not None
    # the drill starts at the cap plane (z=10), not the default z=0
    assert made[0].center == (10, 10, 10.0)
    assert made[0].axis == "Z"
