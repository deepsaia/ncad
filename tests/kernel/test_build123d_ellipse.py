import math

import pytest

pytestmark = pytest.mark.slow


def test_full_ellipse_edge_is_closed():
    from build123d import Plane

    from ncad.kernel.build123d_kernel import _build_edge

    edge = _build_edge(
        {"kind": "ellipse", "center": (0.0, 0.0), "major_axis_end": (5.0, 0.0),
         "minor_radius": 2.0}, Plane.XY)
    assert edge.is_closed
    # Major radius 5, minor 2: circumference is between the two circle bounds.
    assert 2 * math.pi * 2.0 < edge.length < 2 * math.pi * 5.0


def test_ellipse_arc_edge_is_open_quarter():
    from build123d import Plane

    from ncad.kernel.build123d_kernel import _build_edge

    # Quarter arc from major-axis end (5,0) to minor-axis end (0,2).
    edge = _build_edge(
        {"kind": "ellipse_arc", "center": (0.0, 0.0), "major_axis_end": (5.0, 0.0),
         "minor_radius": 2.0, "points": [(5.0, 0.0), (0.0, 2.0)]}, Plane.XY)
    assert not edge.is_closed
    assert edge.length > 0


def test_ellipse_major_axis_orientation():
    from build123d import Plane

    from ncad.kernel.build123d_kernel import _build_edge

    # Major axis along +Y (major_axis_end straight up): the widest extent is in Y.
    edge = _build_edge(
        {"kind": "ellipse", "center": (0.0, 0.0), "major_axis_end": (0.0, 5.0),
         "minor_radius": 2.0}, Plane.XY)
    bb = edge.bounding_box()
    assert bb.size.Y > bb.size.X   # major axis is vertical
