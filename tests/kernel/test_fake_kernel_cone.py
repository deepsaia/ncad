import math

import pytest

from tests.kernel.fake_kernel import FakeKernel


def test_cone_frustum_volume():
    # Frustum bottom dia 6 (r=3), top dia 12 (R=6), length 3.
    k = FakeKernel()
    cone = k.cone((0.0, 0.0, 0.0), "Z", 6.0, 12.0, 3.0)
    expected = math.pi / 3.0 * 3.0 * (3.0**2 + 3.0 * 6.0 + 6.0**2)
    assert k.volume(cone) == pytest.approx(expected, rel=1e-9)


def test_cone_pointed_tip_volume():
    # top dia 0 >> a true cone: pi/3 * r^2 * h.
    k = FakeKernel()
    cone = k.cone((0.0, 0.0, 0.0), "Z", 6.0, 0.0, 3.0)
    assert k.volume(cone) == pytest.approx(math.pi / 3.0 * 3.0**2 * 3.0, rel=1e-9)
