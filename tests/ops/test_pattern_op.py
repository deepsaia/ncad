import pytest

from ncad.kernel.body_set import BodySet
from ncad.ops.pattern_op import PatternOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_linear_merge_false_yields_n_body_bodyset_with_ordinal_ids():
    k = FakeKernel()
    box = _box(k)  # volume 1000
    result = PatternOp().build(
        box, {"id": "grid", "kind": "linear", "merge": False,
              "x": {"dir": [1, 0, 0], "spacing": 20, "count": 2},
              "y": {"dir": [0, 1, 0], "spacing": 20, "count": 2}}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert result.shape.ids() == ["grid/body/0", "grid/body/1", "grid/body/2", "grid/body/3"]
    assert k.volume(result.shape) == pytest.approx(4000.0)  # 4 * 1000


def test_linear_merge_true_fuses_to_single_shape():
    k = FakeKernel()
    box = _box(k)
    result = PatternOp().build(
        box, {"id": "grid", "kind": "linear",
              "x": {"dir": [1, 0, 0], "spacing": 20, "count": 4}}, {}, k)
    assert not isinstance(result.shape, BodySet)
    assert k.volume(result.shape) == pytest.approx(4000.0)  # 4 * 1000, fused (fake sums)


def test_circular_merge_true_replicates_count():
    k = FakeKernel()
    box = _box(k)
    result = PatternOp().build(
        box, {"id": "ring", "kind": "circular", "count": 6}, {}, k)
    assert not isinstance(result.shape, BodySet)
    assert k.volume(result.shape) == pytest.approx(6000.0)  # 6 * 1000


def test_circular_rotate_false_uses_bbox_anchor():
    k = FakeKernel()
    box = _box(k)  # bbox center (5,5,5)
    result = PatternOp().build(
        box, {"id": "ring", "kind": "circular", "count": 4, "rotate": False,
              "merge": False}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert len(result.shape) == 4  # anchor supplied by op, no ValueError


def test_no_solid_reports_issue():
    k = FakeKernel()
    result = PatternOp().build(
        None, {"id": "grid", "kind": "linear",
               "x": {"dir": [1, 0, 0], "spacing": 20, "count": 2}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_bad_params_report_issue():
    k = FakeKernel()
    box = _box(k)
    result = PatternOp().build(box, {"id": "grid", "kind": "spiral"}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
