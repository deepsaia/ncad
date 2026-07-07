import pytest

from tests.kernel.fake_kernel import FakeKernel


def _square(k, side, offset):
    h = side / 2.0
    return k.polygon_face([(-h, -h), (h, -h), (h, h), (-h, h)], "XY", offset=offset)


def test_loft_equal_sections_is_prism_volume():
    # Two equal 2x2 squares (area 4) at offsets 0 and 10 >> prism volume 4 * 10.
    k = FakeKernel()
    solid = k.loft([_square(k, 2, 0.0), _square(k, 2, 10.0)])
    assert k.volume(solid) == pytest.approx(4 * 10, rel=1e-9)


def test_loft_trapezoid_for_differing_sections():
    # Areas 4 (2x2 at 0) and 16 (4x4 at 10) >> (4 + 16)/2 * 10 = 100.
    k = FakeKernel()
    solid = k.loft([_square(k, 2, 0.0), _square(k, 4, 10.0)])
    assert k.volume(solid) == pytest.approx((4 + 16) / 2 * 10, rel=1e-9)


def test_loft_point_cap_is_cone_like():
    # One 2x2 square (area 4) at offset 0 lofted to a point at z=9 >> (4 + 0)/2 * 9 = 18.
    k = FakeKernel()
    solid = k.loft([_square(k, 2, 0.0)], end_point=(0.0, 0.0, 9.0))
    assert k.volume(solid) == pytest.approx((4 + 0) / 2 * 9, rel=1e-9)


def test_loft_ruled_does_not_change_fake_volume():
    k = FakeKernel()
    smooth = k.volume(k.loft([_square(k, 2, 0.0), _square(k, 2, 10.0)]))
    ruled = k.volume(k.loft([_square(k, 2, 0.0), _square(k, 2, 10.0)], ruled=True))
    assert ruled == pytest.approx(smooth, rel=1e-9)
