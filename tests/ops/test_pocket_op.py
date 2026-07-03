import pytest

from ncad.ops.pocket_op import PocketOp
from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _rect(id_, w, h):
    return {"id": id_, "op": "sketch", "plane": "XY",
            "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}


def test_pocket_cuts_from_solid() -> None:
    kernel = FakeKernel()
    base_face = SketchOp().build(None, _rect("sk", 80, 60), {}, kernel).shape
    solid = kernel.extrude(base_face, 8.0)
    tool_face = SketchOp().build(None, _rect("cut", 20, 20), {}, kernel).shape

    feature = {"id": "pkt", "op": "pocket", "profile": "cut", "distance": 8.0,
               "__shapes__": {"cut": tool_face}}
    result = PocketOp().build(solid, feature, {}, kernel)

    assert result.issues == []
    assert kernel.volume(result.shape) == pytest.approx(80 * 60 * 8 - 20 * 20 * 8)


def test_pocket_without_solid_reports_issue() -> None:
    kernel = FakeKernel()
    tool_face = SketchOp().build(None, _rect("cut", 20, 20), {}, kernel).shape
    feature = {"id": "pkt", "op": "pocket", "profile": "cut", "distance": 8.0,
               "__shapes__": {"cut": tool_face}}

    result = PocketOp().build(None, feature, {}, kernel)

    assert result.shape is None
    assert result.issues[0].node_id == "pkt"
