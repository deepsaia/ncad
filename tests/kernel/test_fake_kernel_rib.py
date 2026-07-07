import pytest

from tests.kernel.fake_kernel import FakeKernel


def test_rib_volume_is_length_times_thickness_times_depth():
    # A straight wire of length 20 (from -10 to 10), thickness 3, depth 20 >> 20*3*20.
    k = FakeKernel()
    wire = k.wire([{"kind": "line", "points": [(-10.0, 0.0), (10.0, 0.0)]}], "XZ")
    blade = k.rib(wire, thickness=3.0, depth=20.0)
    assert k.volume(blade) == pytest.approx(20 * 3 * 20, rel=1e-9)


def test_rib_volume_scales_with_total_wire_length():
    # Two segments: length 10 + 10 = 20 total.
    k = FakeKernel()
    wire = k.wire([{"kind": "line", "points": [(0.0, 0.0), (10.0, 0.0)]},
                   {"kind": "line", "points": [(10.0, 0.0), (10.0, 10.0)]}], "XZ")
    blade = k.rib(wire, thickness=2.0, depth=5.0)
    assert k.volume(blade) == pytest.approx(20 * 2 * 5, rel=1e-9)


def test_rib_volume_is_positive():
    k = FakeKernel()
    wire = k.wire([{"kind": "line", "points": [(0.0, 0.0), (4.0, 0.0)]}], "XZ")
    assert k.volume(k.rib(wire, thickness=1.0, depth=3.0)) > 0
