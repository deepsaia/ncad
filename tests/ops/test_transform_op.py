from ncad.kernel.body_set import BodySet
from ncad.ops.transform_op import TransformOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), distance=10)


def test_transform_in_place_returns_single_shape():
    k = FakeKernel()
    box = _box(k)
    result = TransformOp().build(box, {"id": "mv", "move": [20, 0, 0]}, {}, k)
    assert result.shape is not None
    assert not isinstance(result.shape, BodySet)  # in place: one shape
    assert k.volume(result.shape) == 1000.0


def test_transform_copy_yields_two_body_bodyset():
    k = FakeKernel()
    box = _box(k)
    result = TransformOp().build(
        box, {"id": "cp", "move": [20, 0, 0], "scale": 2, "copy": True}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert len(result.shape) == 2
    assert result.shape.ids() == ["cp/body/0", "cp/body/1"]


def test_transform_no_solid_reports_issue():
    k = FakeKernel()
    result = TransformOp().build(None, {"id": "mv", "move": [1, 0, 0]}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_transform_bad_params_report_issue():
    k = FakeKernel()
    box = _box(k)
    result = TransformOp().build(box, {"id": "mv"}, {}, k)  # nothing to do
    assert result.shape is None and any(i.level == "error" for i in result.issues)
