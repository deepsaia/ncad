import math

import pytest

from tests.kernel.fake_kernel import FakeKernel


def _offset_rect(kernel):
    # a 4 (x) by 2 (y) rectangle whose centroid sits at x=10, revolved about Y (the global
    # Y axis through the origin) => a washer; Pappus volume = area * 2pi * 10.
    return kernel.polygon_face([(8, 0), (12, 0), (12, 2), (8, 2)], "XY")


def test_full_revolve_pappus_volume():
    k = FakeKernel()
    solid = k.revolve(_offset_rect(k), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert k.volume(solid) == pytest.approx(8 * 2 * math.pi * 10, rel=1e-9)


def test_partial_angle_scales_linearly():
    k = FakeKernel()
    full = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0)))
    quarter = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0), angle=90))
    assert quarter == pytest.approx(full / 4, rel=1e-9)


def test_thin_reduces_volume():
    k = FakeKernel()
    full = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0)))
    thin = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0), thin=0.5))
    assert 0 < thin < full
