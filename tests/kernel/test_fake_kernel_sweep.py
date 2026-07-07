import math

import pytest

from tests.kernel.fake_kernel import FakeKernel


def _square(k):
    return k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY")


def _straight_path(k):
    return k.wire([{"kind": "line", "points": [(0.0, 0.0), (0.0, 10.0)]}], "XZ")


def test_sweep_volume_is_area_times_length():
    k = FakeKernel()
    solid = k.sweep(_square(k), _straight_path(k))
    assert k.volume(solid) == pytest.approx(2 * 2 * 10, rel=1e-9)


def test_helix_path_length_analytic():
    k = FakeKernel()
    path = k.helix_path(5.0, 40.0, 12.0, axis_point=(0, 0, 0), axis_dir=(0, 0, 1))
    turns = 40.0 / 5.0
    expected = turns * math.sqrt((2 * math.pi * 12.0) ** 2 + 5.0 ** 2)
    assert k.wire_length(path) == pytest.approx(expected, rel=1e-9)


def test_sweep_along_helix_volume():
    k = FakeKernel()
    path = k.helix_path(5.0, 40.0, 12.0, axis_point=(0, 0, 0), axis_dir=(0, 0, 1))
    solid = k.sweep(_square(k), path)
    assert k.volume(solid) == pytest.approx(4 * k.wire_length(path), rel=1e-9)


def test_sweep_sections_use_mean_area():
    k = FakeKernel()
    big = k.polygon_face([(0, 0), (4, 0), (4, 4), (0, 4)], "XY")  # area 16
    small = _square(k)  # area 4
    solid = k.sweep(big, _straight_path(k), sections=[big, small])
    assert k.volume(solid) == pytest.approx(((16 + 4) / 2) * 10, rel=1e-9)
