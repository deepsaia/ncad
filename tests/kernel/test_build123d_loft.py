import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def test_loft_two_sections_builds_solid():
    k = _kernel()
    bottom = k.polygon_face([(-2, -2), (2, -2), (2, 2), (-2, 2)], "XY", offset=0.0)
    top = k.circle_face((0.0, 0.0), 3.0, "XY", offset=20.0)
    solid = k.loft([bottom, top])
    assert k.volume(solid) > 0


def test_loft_point_cap_builds():
    k = _kernel()
    base = k.circle_face((0.0, 0.0), 6.0, "XY", offset=0.0)
    solid = k.loft([base], end_point=(0.0, 0.0, 15.0))
    assert k.volume(solid) > 0


def test_loft_ruled_builds():
    k = _kernel()
    bottom = k.polygon_face([(-2, -2), (2, -2), (2, 2), (-2, 2)], "XY", offset=0.0)
    top = k.polygon_face([(-1, -1), (1, -1), (1, 1), (-1, 1)], "XY", offset=10.0)
    solid = k.loft([bottom, top], ruled=True)
    assert k.volume(solid) > 0
