
import pytest

pytestmark = pytest.mark.slow


def test_oriented_bbox_recovers_true_dimensions_when_rotated():
    from build123d import Axis, Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    bar = Solid.make_box(20, 10, 5).rotate(Axis.Z, 37.0).rotate(Axis.X, 22.0)
    obb = kernel.oriented_bounding_box(bar)
    # The min box recovers the bar's true dimensions regardless of world orientation.
    assert sorted(round(s, 3) for s in obb["size"]) == [5.0, 10.0, 20.0]
    # And it is no larger than the axis-aligned bbox (tighter or equal on every axis span).
    (lo, hi) = kernel.bounding_box(bar)
    aabb = sorted([hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]])
    obb_sorted = sorted(obb["size"])
    assert all(o <= a + 1e-6 for o, a in zip(obb_sorted, aabb))
