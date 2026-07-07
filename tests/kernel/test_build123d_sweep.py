import math

import pytest


def _circle(k):
    return k.circle_face((0.0, 0.0), 4.0, "XY")  # d=4 => r=2, area = 4pi


@pytest.mark.slow
def test_sweep_along_straight_wire():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    path = k.wire([{"kind": "line", "points": [(0.0, 0.0), (0.0, 20.0)]}], "XZ")
    solid = k.sweep(_circle(k), path)
    assert k.volume(solid) == pytest.approx(math.pi * 4 * 20, rel=1e-3)


@pytest.mark.slow
def test_sweep_along_helix_builds():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    path = k.helix_path(5.0, 40.0, 12.0, axis_point=(0, 0, 0), axis_dir=(0, 0, 1))
    solid = k.sweep(_circle(k), path)
    assert k.volume(solid) > 0


@pytest.mark.slow
def test_sweep_rounded_corner_sweeps_full_length():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    # a rounded L: vertical line, arc corner, horizontal line (a sharp L drops the leg)
    path = k.wire([
        {"kind": "line", "points": [(0.0, 0.0), (0.0, 15.0)]},
        {"kind": "arc", "points": [(0.0, 15.0), (2.0, 18.0), (5.0, 20.0)]},
        {"kind": "line", "points": [(5.0, 20.0), (20.0, 20.0)]},
    ], "XZ")
    solid = k.sweep(_circle(k), path)
    # the whole path (>30 long) is swept, so volume clearly exceeds the first leg alone
    assert k.volume(solid) > math.pi * 4 * 20
