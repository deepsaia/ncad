import pytest

pytestmark = pytest.mark.slow


def test_conic_parabola_builds_open_edge():
    from build123d import Plane

    from ncad.kernel.build123d_kernel import _build_edge

    edge = _build_edge(
        {"kind": "conic", "points": [(0.0, 0.0), (5.0, 5.0), (10.0, 0.0)], "rho": 0.5},
        Plane.XY)
    assert not edge.is_closed
    assert edge.length > 10.0   # bows up through the apex, longer than the 10-unit chord


def test_conic_rho_changes_bulge():
    from build123d import Plane

    from ncad.kernel.build123d_kernel import _build_edge

    ellipse_like = _build_edge(
        {"kind": "conic", "points": [(0.0, 0.0), (5.0, 5.0), (10.0, 0.0)], "rho": 0.3},
        Plane.XY)
    hyperbola_like = _build_edge(
        {"kind": "conic", "points": [(0.0, 0.0), (5.0, 5.0), (10.0, 0.0)], "rho": 0.8},
        Plane.XY)
    # Higher rho pulls the curve closer to the apex -> longer arc.
    assert hyperbola_like.length > ellipse_like.length
