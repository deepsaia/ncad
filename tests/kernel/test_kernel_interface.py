"""Tests for the abstract Kernel contract.

The Kernel deals in opaque solid handles, so the Builder never depends on a concrete
backend. These tests use a tiny in-memory fake to confirm the contract is satisfiable
without importing the heavy OCP backend.
"""

import pytest

from ncad.kernel.kernel import Kernel


def test_kernel_is_abstract() -> None:
    with pytest.raises(TypeError):
        Kernel()  # cannot instantiate an abstract class


def test_fake_kernel_satisfies_contract() -> None:
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    box = kernel.box(center=(0.0, 0.0, 0.0), size=(2.0, 2.0, 2.0))

    assert kernel.volume(box) == pytest.approx(8.0, rel=0.05)
    union = kernel.union([box, kernel.box(center=(5.0, 0.0, 0.0), size=(2.0, 2.0, 2.0))])
    assert kernel.volume(union) > 0
    diff = kernel.subtract(union, [kernel.box(center=(0.0, 0.0, 0.0), size=(1.0, 1.0, 1.0))])
    assert kernel.volume(diff) < kernel.volume(union)


def test_fake_kernel_prism_volume() -> None:
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    # Triangular cross-section (base 6 at z=0, apex at z=2), extruded along x for length 8.
    # Volume = (0.5 * 6 * 2) * 8 = 48.
    profile = [(0.0, 0.0), (6.0, 0.0), (3.0, 2.0)]
    prism = kernel.prism(profile=profile, axis="x", start=0.0, end=8.0)

    assert kernel.volume(prism) == pytest.approx(48.0, rel=0.1)
    (minx, _, minz), (maxx, _, maxz) = kernel.bounding_box(prism)
    assert (minx, maxx) == pytest.approx((0.0, 8.0))
    assert (minz, maxz) == pytest.approx((0.0, 2.0))


def test_fake_kernel_extrude_polygon_square_matches_box() -> None:
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    # A 4x4 square footprint extruded 3m tall = 48 m^3, same as the equivalent box.
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    solid = kernel.extrude_polygon(polygon=square, base_z=0.0, height=3.0)

    assert kernel.volume(solid) == pytest.approx(48.0, rel=0.05)
    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == pytest.approx((0.0, 0.0, 0.0))
    assert (maxx, maxy, maxz) == pytest.approx((4.0, 4.0, 3.0))


def test_fake_kernel_extrude_polygon_l_shape_excludes_notch() -> None:
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    # L-shape: 6x6 square minus a 3x3 top-right notch. Area = 36 - 9 = 27; height 2 → 54.
    l_shape = [(0, 0), (6, 0), (6, 3), (3, 3), (3, 6), (0, 6)]
    solid = kernel.extrude_polygon(polygon=l_shape, base_z=0.0, height=2.0)

    assert kernel.volume(solid) == pytest.approx(54.0, rel=0.1)
    # A point in the notch is NOT inside the solid (bounding box would wrongly include it).
    assert not kernel._point_inside(solid, 4.5, 4.5, 1.0)
