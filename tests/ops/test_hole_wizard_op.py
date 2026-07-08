import math

import pytest

from ncad.ops.hole_op import HoleOp
from tests.kernel.fake_kernel import FakeKernel


def _plate(k):
    return k.extrude(k.polygon_face([(0, 0), (40, 0), (40, 40), (0, 40)], "XY"),
                     distance=20.0)


def test_simple_hole_still_drills():
    k = FakeKernel()
    plate = _plate(k)
    result = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "diameter": 6,
                "through": True}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) < k.volume(plate)


def test_counterbore_removes_more_than_simple():
    k = FakeKernel()
    plate = _plate(k)
    simple = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "diameter": 6,
                "depth": 20}, {}, k)
    cbore = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "diameter": 6,
                "depth": 20, "counterbore": {"diameter": 12, "depth": 5}}, {}, k)
    assert k.volume(cbore.shape) < k.volume(simple.shape)


def test_countersink_removes_more_than_simple():
    k = FakeKernel()
    plate = _plate(k)
    simple = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "diameter": 6,
                "depth": 20}, {}, k)
    csink = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "diameter": 6,
                "depth": 20, "countersink": {"diameter": 12, "angle": 82}}, {}, k)
    assert k.volume(csink.shape) < k.volume(simple.shape)


def test_sized_hole_resolves_diameter():
    # M6 normal >> 6.6 dia; the removed cylinder volume matches pi*(6.6/2)^2*depth.
    k = FakeKernel()
    plate = _plate(k)
    result = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]], "size": "M6",
                "fit": "normal", "depth": 20}, {}, k)
    removed = k.volume(plate) - k.volume(result.shape)
    assert removed == pytest.approx(math.pi * (6.6 / 2) ** 2 * 20, rel=1e-9)


def test_bad_params_report_issue():
    k = FakeKernel()
    plate = _plate(k)
    result = HoleOp().build(
        plate, {"id": "h", "plane": "XY", "positions": [[20, 20]],
                "counterbore": {"diameter": 12, "depth": 5},
                "countersink": {"diameter": 12}, "diameter": 6, "depth": 20}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
