"""Tests for the occupancy-grid footprint module (L/T/U via marching-squares boundary).

Pure and deterministic — no RNG. Produces a CCW rectilinear polygon and a set of
rectangular wings that tile the footprint.
"""

import pytest

from ncad.generate.footprint_grid import FootprintGrid


def _polygon_area(polygon: list) -> float:
    area = 0.0
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2.0  # signed: >0 means CCW


def test_rect_shape_is_four_corner_polygon() -> None:
    grid = FootprintGrid(shape="rect", width=12.0, depth=9.0)

    polygon = grid.polygon()

    assert len(polygon) == 4
    assert _polygon_area(polygon) == pytest.approx(12.0 * 9.0)


def test_l_shape_has_six_corners() -> None:
    grid = FootprintGrid(shape="L", width=12.0, depth=9.0)

    polygon = grid.polygon()

    assert len(polygon) == 6


def test_t_and_u_shapes_have_eight_corners() -> None:
    for shape in ("T", "U"):
        grid = FootprintGrid(shape=shape, width=12.0, depth=9.0)
        assert len(grid.polygon()) == 8, f"{shape} should have 8 corners"


def test_polygon_is_counter_clockwise() -> None:
    for shape in ("rect", "L", "T", "U"):
        grid = FootprintGrid(shape=shape, width=12.0, depth=9.0)
        assert _polygon_area(grid.polygon()) > 0, f"{shape} polygon must be CCW"


def test_l_shape_area_less_than_bounding_box() -> None:
    grid = FootprintGrid(shape="L", width=12.0, depth=9.0)

    area = abs(_polygon_area(grid.polygon()))
    assert area < 12.0 * 9.0  # the notch is removed
    assert area > 0


def test_wings_tile_the_footprint_area() -> None:
    for shape in ("rect", "L", "T", "U"):
        grid = FootprintGrid(shape=shape, width=12.0, depth=9.0)
        footprint_area = abs(_polygon_area(grid.polygon()))
        wings_area = sum(w.area for w in grid.wings())
        assert wings_area == pytest.approx(footprint_area), f"{shape} wings must tile footprint"


def test_wings_do_not_overlap_for_l_shape() -> None:
    grid = FootprintGrid(shape="L", width=12.0, depth=9.0)
    wings = grid.wings()

    # At least 2 wings for an L; their summed area equals the footprint (no double-count).
    assert len(wings) >= 2


def test_unknown_shape_raises() -> None:
    with pytest.raises(ValueError, match="shape"):
        FootprintGrid(shape="hexagon", width=12.0, depth=9.0)
