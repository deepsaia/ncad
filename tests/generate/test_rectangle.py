"""Tests for the Rectangle geometry value type (pure, no randomness)."""

import pytest

from ncad.generate.rectangle import Rectangle


def test_dimensions_and_area() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    assert rect.width == 8.0
    assert rect.height == 6.0
    assert rect.area == 48.0


def test_longer_axis_is_x_when_wider() -> None:
    assert Rectangle(0.0, 0.0, 8.0, 6.0).longer_axis == "x"


def test_longer_axis_is_y_when_taller() -> None:
    assert Rectangle(0.0, 0.0, 4.0, 10.0).longer_axis == "y"


def test_corners_are_counter_clockwise_polygon() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    assert rect.corners() == [(0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)]


def test_split_x_produces_left_right_and_vertical_segment() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    left, right, segment = rect.split("x", 5.0)

    assert left == Rectangle(0.0, 0.0, 5.0, 6.0)
    assert right == Rectangle(5.0, 0.0, 8.0, 6.0)
    assert segment == ((5.0, 0.0), (5.0, 6.0))


def test_split_y_produces_bottom_top_and_horizontal_segment() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    bottom, top, segment = rect.split("y", 2.0)

    assert bottom == Rectangle(0.0, 0.0, 8.0, 2.0)
    assert top == Rectangle(0.0, 2.0, 8.0, 6.0)
    assert segment == ((0.0, 2.0), (8.0, 2.0))


def test_split_outside_bounds_raises() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    with pytest.raises(ValueError):
        rect.split("x", 9.0)


def test_split_unknown_axis_raises() -> None:
    rect = Rectangle(0.0, 0.0, 8.0, 6.0)

    with pytest.raises(ValueError):
        rect.split("z", 4.0)
