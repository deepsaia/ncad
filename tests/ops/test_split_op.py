import pytest

from ncad.kernel.body_set import BodySet
from ncad.ops.split_op import SplitOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_split_both_yields_two_body_bodyset_with_ordinal_ids():
    k = FakeKernel()
    result = SplitOp().build(_box(k), {"id": "halves", "plane": "YZ", "plane_offset": 5}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert result.shape.ids() == ["halves/body/0", "halves/body/1"]
    assert k.volume(result.shape) == pytest.approx(1000.0)


def test_split_top_yields_single_shape():
    k = FakeKernel()
    result = SplitOp().build(
        _box(k), {"id": "h", "plane": "YZ", "plane_offset": 2, "keep": "top"}, {}, k)
    assert not isinstance(result.shape, BodySet)
    assert k.volume(result.shape) == pytest.approx(800.0)


def test_no_solid_reports_issue():
    k = FakeKernel()
    result = SplitOp().build(None, {"id": "h", "plane": "YZ"}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_bad_params_report_issue():
    k = FakeKernel()
    result = SplitOp().build(_box(k), {"id": "h", "plane": "AB"}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
