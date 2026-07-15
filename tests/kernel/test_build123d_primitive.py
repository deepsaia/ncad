import math

import pytest

pytestmark = pytest.mark.slow

_CASES = [
    ("box", {"w": 10.0, "d": 10.0, "h": 10.0}, 1000.0),
    ("sphere", {"radius": 10.0}, 4.0 / 3.0 * math.pi * 1000.0),
    ("cylinder", {"radius": 5.0, "h": 20.0}, math.pi * 25.0 * 20.0),
    ("cone", {"bottom_radius": 10.0, "top_radius": 0.0, "h": 20.0}, math.pi / 3.0 * 20.0 * 100.0),
    ("torus", {"major_radius": 30.0, "minor_radius": 4.0}, 2.0 * math.pi ** 2 * 30.0 * 16.0),
    ("wedge", {"dx": 20.0, "dy": 10.0, "dz": 15.0}, 3000.0),
]


@pytest.mark.parametrize("kind, dims, expected", _CASES)
def test_primitive_volume_matches_analytic(kind, dims, expected):
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    solid = kernel.make_primitive(kind, dims, "XY", (0.0, 0.0))
    assert solid.is_valid
    assert math.isclose(kernel.volume(solid), expected, rel_tol=1e-4)
