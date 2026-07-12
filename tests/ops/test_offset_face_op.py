from ncad.ops.offset_face_op import OffsetFaceOp
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, h=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"), h)


def test_offset_outward_succeeds() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    result = OffsetFaceOp().build(solid, {"id": "of", "distance": 1.0, "__refs__": {}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_offset_inward_past_wall_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)  # min wall 20
    result = OffsetFaceOp().build(solid, {"id": "of", "distance": -25.0, "__refs__": {}},
                                  {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "of"
