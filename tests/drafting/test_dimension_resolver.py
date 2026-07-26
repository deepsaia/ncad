"""DimensionResolver: measure a dimension from projected 2D edges (no kernel; fixture edges)."""

import math

from ncad.drafting.dimension_resolver import DimensionResolver


def test_linear_between_two_parallel_edges():
    # Two vertical edges 40 apart in the view plane.
    left = [(0.0, 0.0), (0.0, 60.0)]
    right = [(40.0, 0.0), (40.0, 60.0)]
    dim = DimensionResolver().measure_linear([left, right])
    assert dim["value"] == 40.0
    assert "geometry" in dim


def test_linear_between_two_points():
    # A degenerate "edge" set of single points still measures the span.
    dim = DimensionResolver().measure_linear([[(10.0, 10.0)], [(10.0, 34.0)]])
    assert dim["value"] == 24.0


def test_diameter_from_a_circle_polyline():
    # A polyline sampling a circle of radius 4 centered at origin.
    circle = [(4.0 * math.cos(t), 4.0 * math.sin(t))
              for t in [i * math.pi / 8 for i in range(16)]]
    dim = DimensionResolver().measure_diameter(circle)
    assert round(dim["value"], 3) == 8.0


def test_radius_from_a_circle_polyline():
    circle = [(5.0 * math.cos(t), 5.0 * math.sin(t))
              for t in [i * math.pi / 8 for i in range(16)]]
    dim = DimensionResolver().measure_radius(circle)
    assert round(dim["value"], 3) == 5.0
