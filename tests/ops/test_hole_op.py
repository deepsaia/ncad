import pytest

from ncad.ops.hole_op import HoleOp
from ncad.ops.sketch_op import SketchOp
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
