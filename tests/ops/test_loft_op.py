import pytest

from ncad.ops.loft_op import LoftOp
from tests.kernel.fake_kernel import FakeKernel


def _square(k, side, offset):
    h = side / 2.0
    return k.polygon_face([(-h, -h), (h, -h), (h, h), (-h, h)], "XY", offset=offset)


def test_loft_two_sections_builds():
    k = FakeKernel()
    s0, s1 = _square(k, 2, 0.0), _square(k, 2, 10.0)
    result = LoftOp().build(
        None, {"id": "lf", "__refs__": {"sections": [s0, s1]}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) == pytest.approx(4 * 10, rel=1e-9)


def test_loft_point_cap_builds():
    k = FakeKernel()
    s0 = _square(k, 2, 0.0)
    result = LoftOp().build(
        None, {"id": "lf", "end_point": [0, 0, 9], "__refs__": {"sections": [s0]}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) == pytest.approx((4 + 0) / 2 * 9, rel=1e-9)


def test_loft_one_section_no_cap_reports_issue():
    k = FakeKernel()
    s0 = _square(k, 2, 0.0)
    result = LoftOp().build(
        None, {"id": "lf", "__refs__": {"sections": [s0]}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
