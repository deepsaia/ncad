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
