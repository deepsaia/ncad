from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def test_sketch_passes_plane_offset_to_kernel():
    k = FakeKernel()
    params = {"id": "sk", "op": "sketch", "plane": "XY", "plane_offset": 30,
              "elements": [{"id": "r", "type": "rectangle", "w": 4, "h": 2}]}
    result = SketchOp().build(None, params, {}, k)
    assert result.shape is not None
    assert result.shape.offset == 30.0


def test_sketch_offset_defaults_zero():
    k = FakeKernel()
    params = {"id": "sk", "op": "sketch", "plane": "XY",
              "elements": [{"id": "c", "type": "circle", "d": 6}]}
    result = SketchOp().build(None, params, {}, k)
    assert result.shape.offset == 0.0
