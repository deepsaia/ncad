"""Tests for the seeded BSP room subdivider.

All randomness arrives via an injected random.Random, so these tests are fully
deterministic by constructing their own seeded RNG.
"""

import random

import pytest

from ncad.generate.bsp_subdivider import BspSubdivider
from ncad.generate.rectangle import Rectangle

_FOOTPRINT = Rectangle(0.0, 0.0, 12.0, 9.0)


def _subdivide(seed: int, num_rooms: int, min_room_size: float = 2.0):
    subdivider = BspSubdivider(num_rooms=num_rooms, min_room_size=min_room_size)
    return subdivider.subdivide(_FOOTPRINT, random.Random(seed))


def test_single_room_is_the_footprint_with_no_interior_walls() -> None:
    result = _subdivide(seed=1, num_rooms=1)

    assert result.rooms == [_FOOTPRINT]
    assert result.interior_walls == []


def test_produces_requested_room_count() -> None:
    result = _subdivide(seed=1, num_rooms=4)

    assert len(result.rooms) == 4


def test_interior_wall_count_is_rooms_minus_one() -> None:
    result = _subdivide(seed=7, num_rooms=4)

    assert len(result.interior_walls) == len(result.rooms) - 1


def test_is_deterministic_for_same_seed() -> None:
    a = _subdivide(seed=42, num_rooms=5)
    b = _subdivide(seed=42, num_rooms=5)

    assert a.rooms == b.rooms
    assert a.interior_walls == b.interior_walls


def test_different_seed_changes_layout() -> None:
    a = _subdivide(seed=1, num_rooms=5)
    b = _subdivide(seed=2, num_rooms=5)

    assert a.rooms != b.rooms


def test_rooms_tile_the_footprint_area() -> None:
    result = _subdivide(seed=3, num_rooms=6)

    total = sum(room.area for room in result.rooms)
    assert total == pytest.approx(_FOOTPRINT.area)


def test_rooms_respect_min_room_size() -> None:
    result = _subdivide(seed=9, num_rooms=6, min_room_size=2.0)

    for room in result.rooms:
        assert room.width >= 2.0
        assert room.height >= 2.0


def test_stops_early_when_min_room_size_prevents_more_splits() -> None:
    # Footprint can't yield 100 rooms at 2m min; should produce fewer, all valid.
    result = _subdivide(seed=1, num_rooms=100, min_room_size=2.0)

    assert len(result.rooms) < 100
    for room in result.rooms:
        assert room.width >= 2.0 and room.height >= 2.0
