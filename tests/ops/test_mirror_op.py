import pytest

from ncad.kernel.body_set import BodySet
from ncad.ops.mirror_op import MirrorOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_keep_true_merge_false_yields_two_body_bodyset_ordinal_ids():
    k = FakeKernel()
    box = _box(k)  # volume 1000
    result = MirrorOp().build(
        box, {"id": "sym", "plane": "YZ", "keep": True, "merge": False}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert result.shape.ids() == ["sym/body/0", "sym/body/1"]
    assert k.volume(result.shape) == pytest.approx(2000.0)  # original + reflection


def test_keep_true_merge_true_fuses_to_single_shape():
    k = FakeKernel()
    box = _box(k)
    result = MirrorOp().build(box, {"id": "sym", "plane": "YZ"}, {}, k)  # defaults
    assert not isinstance(result.shape, BodySet)
    assert k.volume(result.shape) == pytest.approx(2000.0)  # fake fuse sums


def test_keep_false_reflects_in_place_single_shape():
    k = FakeKernel()
    box = _box(k)
    result = MirrorOp().build(box, {"id": "flip", "plane": "YZ", "keep": False}, {}, k)
    assert not isinstance(result.shape, BodySet)
    assert k.volume(result.shape) == pytest.approx(1000.0)  # only the reflection
    (minx, _, _), (maxx, _, _) = k.bounding_box(result.shape)
    assert minx == pytest.approx(-10.0) and maxx == pytest.approx(0.0)


def test_no_solid_reports_issue():
    k = FakeKernel()
    result = MirrorOp().build(None, {"id": "sym", "plane": "YZ"}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_bad_params_report_issue():
    k = FakeKernel()
    box = _box(k)
    result = MirrorOp().build(box, {"id": "sym", "plane": "AB"}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
