"""Tests for the world->SVG coordinate transform.

World is meters, Y-up (north = +Y). SVG is pixels, Y-down. The transform scales to fit a
target size with a margin and flips Y so north points up in the image.
"""

from ncad.render.plan_transform import PlanTransform


def test_origin_maps_to_bottom_left_inside_margin() -> None:
    # 10m x 10m world, 100px canvas hint, 10px margin -> 80px drawable.
    transform = PlanTransform(world_width=10.0, world_height=10.0, size=100.0, margin=10.0)

    x, y = transform.point(0.0, 0.0)

    assert x == 10.0  # left margin
    assert y == 90.0  # bottom (Y flipped): size - margin


def test_top_right_world_maps_to_top_right_pixels() -> None:
    transform = PlanTransform(world_width=10.0, world_height=10.0, size=100.0, margin=10.0)

    x, y = transform.point(10.0, 10.0)

    assert x == 90.0  # right: size - margin
    assert y == 10.0  # top (Y flipped): margin


def test_uniform_scale_preserves_aspect_ratio() -> None:
    # Wide world (20x10): scale fixed by the wider axis so it isn't distorted.
    transform = PlanTransform(world_width=20.0, world_height=10.0, size=100.0, margin=10.0)

    # 80px drawable / 20m = 4 px/m. A 10m height occupies 40px, centered vertically.
    assert transform.scale == 4.0


def test_canvas_dimensions_match_world_aspect() -> None:
    transform = PlanTransform(world_width=20.0, world_height=10.0, size=100.0, margin=10.0)

    # Width is the limiting axis -> full 100px; height = 10m*4 + 2*10 margin = 60px.
    assert transform.canvas_width == 100.0
    assert transform.canvas_height == 60.0


def test_length_scales_by_scale_factor() -> None:
    transform = PlanTransform(world_width=10.0, world_height=10.0, size=100.0, margin=10.0)

    assert transform.length(2.0) == 16.0  # 2m * 8 px/m
