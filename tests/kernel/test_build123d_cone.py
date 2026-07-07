import math

import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def test_cone_frustum_volume():
    k = _kernel()
    cone = k.cone((0.0, 0.0, 0.0), "Z", 6.0, 12.0, 3.0)
    expected = math.pi / 3.0 * 3.0 * (3.0**2 + 3.0 * 6.0 + 6.0**2)
    assert k.volume(cone) == pytest.approx(expected, rel=1e-3)
