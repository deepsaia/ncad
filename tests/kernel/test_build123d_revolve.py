import math

import pytest


def _offset_rect(k):
    return k.polygon_face([(8, 0), (12, 0), (12, 2), (8, 2)], "XY")


@pytest.mark.slow
def test_full_revolve_pappus_volume():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    solid = k.revolve(_offset_rect(k), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert k.volume(solid) == pytest.approx(8 * 2 * math.pi * 10, rel=1e-3)


@pytest.mark.slow
def test_quarter_revolve_is_quarter_volume():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    full = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0)))
    quarter = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0), angle=90))
    assert quarter == pytest.approx(full / 4, rel=1e-3)


@pytest.mark.slow
def test_symmetric_same_volume_as_partial():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    plain = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0), angle=90))
    sym = k.volume(k.revolve(_offset_rect(k), (0, 0, 0), (0, 1, 0), angle=90,
                             symmetric=True))
    assert sym == pytest.approx(plain, rel=1e-3)
