import math

import pytest

from tests.kernel.fake_kernel import FakeKernel


def _bezier_edge():
    return {"kind": "bezier", "points": [(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 0.0)]}


def test_spline_wire_length_is_polyline_length():
    k = FakeKernel()
    wire = k.wire([_bezier_edge()], "XY")
    expected = (math.hypot(1, 2) + math.hypot(2, 0) + math.hypot(1, -2))
    assert k.wire_length(wire) == pytest.approx(expected, rel=1e-9)


def test_sweep_along_spline_path_has_positive_volume():
    k = FakeKernel()
    profile = k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY")
    path = k.wire([_bezier_edge()], "XZ")
    solid = k.sweep(profile, path)
    assert k.volume(solid) > 0


def test_wire_face_area_includes_spline_interior_points():
    # A closed loop: a spline arcing up from (0,0) to (4,0) via (2,3), closed by a line.
    # The area must reflect the interior point (2,3), not just the two endpoints (which
    # would give a degenerate zero-area sliver).
    k = FakeKernel()
    edges = [
        {"kind": "spline", "points": [(0.0, 0.0), (2.0, 3.0), (4.0, 0.0)]},
        {"kind": "line", "points": [(4.0, 0.0), (0.0, 0.0)]},
    ]
    face = k.wire_face(edges, "XY")
    assert face.area > 0
