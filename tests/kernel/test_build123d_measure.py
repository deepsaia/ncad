import math

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


def test_closest_points_pair_is_consistent_with_distance():
    from build123d import Location, Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    a = Solid.make_box(10, 10, 10)
    b = Solid.make_box(4, 4, 4).moved(Location((25, 0, 0)))
    pa, pb = kernel.closest_points(a, b)
    # The facing points: a's +x face (x=10) and b's -x face (x=25).
    assert math.isclose(pa[0], 10.0, abs_tol=1e-6)
    assert math.isclose(pb[0], 25.0, abs_tol=1e-6)
    # The separation of the pair equals the scalar min distance (consistency invariant).
    assert math.isclose(math.dist(pa, pb), kernel.distance(a, b), abs_tol=1e-6)


def test_inertia_gyradius_matches_box_analytic():
    from build123d import Location, Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    a, b, c = 20.0, 10.0, 5.0
    # Center the box on the world origin so the world-axis gyradius equals the centroidal value
    # k = sqrt((d1^2 + d2^2) / 12) for the two extents perpendicular to each axis (gyradius is
    # measured about the world X/Y/Z axes, so placement matters).
    box = Solid.make_box(a, b, c).moved(Location((-a / 2, -b / 2, -c / 2)))
    inertia = kernel.inertia(box)
    analytic = sorted([math.sqrt((b * b + c * c) / 12.0),
                       math.sqrt((a * a + c * c) / 12.0),
                       math.sqrt((a * a + b * b) / 12.0)])
    assert all(math.isclose(g, x, rel_tol=1e-3)
               for g, x in zip(sorted(inertia["gyradius"]), analytic))


def test_max_fillet_returns_a_feasible_radius():
    import pytest as _pytest
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.kernel.kernel_op_error import KernelOpError

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    edges = box.edges()
    r = kernel.max_fillet(box, edges)
    assert 9.0 < r < 10.0  # about half the 20 dimension
    # A fillet AT the returned radius builds; well above it fails (the validator's contract).
    assert kernel.fillet_edges(box, edges, r * 0.98) is not None
    with _pytest.raises((KernelOpError, Exception)):
        kernel.fillet_edges(box, edges, r * 1.5)
