import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def test_rib_straight_wire_builds_blade():
    # Straight wire length 20, thickness 3, depth 20 >> volume 1200 (planar ribbon).
    k = _kernel()
    wire = k.wire([{"kind": "line", "points": [(-10, 0), (10, 0)]}], "XZ")
    blade = k.rib(wire, thickness=3.0, depth=20.0)
    assert k.volume(blade) == pytest.approx(1200.0, rel=1e-3)


def test_rib_curved_wire_builds():
    k = _kernel()
    wire = k.wire([{"kind": "arc", "points": [(-10, 0), (0, 6), (10, 0)]}], "XZ")
    blade = k.rib(wire, thickness=3.0, depth=20.0)
    assert k.volume(blade) > 0
