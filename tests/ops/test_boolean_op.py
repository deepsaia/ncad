import pytest

from ncad.ops.boolean_op import BooleanOp
from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _solid(kernel, w, h, t):
    face = SketchOp().build(None, {"id": "s", "op": "sketch", "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}, {}, kernel).shape
    return kernel.extrude(face, t)


def _feature(operation, shapes):
    return {"id": "bool", "op": "boolean", "operation": operation,
            "target": "a", "tool": "b", "__shapes__": shapes}


def test_cut() -> None:
    kernel = FakeKernel()
    a, b = _solid(kernel, 80, 60, 8), _solid(kernel, 20, 20, 8)

    result = BooleanOp().build(None, _feature("cut", {"a": a, "b": b}), {}, kernel)

    assert result.issues == []
    assert kernel.volume(result.shape) == pytest.approx(80 * 60 * 8 - 20 * 20 * 8)


def test_union() -> None:
    kernel = FakeKernel()
    a, b = _solid(kernel, 10, 10, 5), _solid(kernel, 10, 10, 5)

    result = BooleanOp().build(None, _feature("union", {"a": a, "b": b}), {}, kernel)

    assert kernel.volume(result.shape) == pytest.approx(1000.0)


def test_missing_operand_reports_issue() -> None:
    kernel = FakeKernel()
    a = _solid(kernel, 10, 10, 5)

    result = BooleanOp().build(None, _feature("cut", {"a": a}), {}, kernel)

    assert result.shape is None
    assert result.issues[0].node_id == "bool"
