"""Seeded binary-space-partition subdivision of a footprint into rooms.

This is the only stochastic part of generation. Randomness arrives via an injected
``random.Random`` (the Generator owns the seed), so the subdivider holds no global
state and is deterministic given that RNG. The algorithm splits the largest remaining
room along its longer axis at a jittered position, until the requested room count is
reached or no room can be split without violating ``min_room_size``.
"""

import logging
import random

from ncad.generate.rectangle import Rectangle
from ncad.generate.subdivision import Subdivision

logger = logging.getLogger(__name__)

# Fraction of the split-axis extent around the center within which the cut may fall.
# 0.0 -> always dead center; 0.5 -> anywhere in the central half. Keeps rooms balanced.
_JITTER_FRACTION = 0.4


class BspSubdivider:
    """Subdivides a rectangular footprint into a target number of room rectangles."""

    def __init__(self, num_rooms: int, min_room_size: float) -> None:
        """:param num_rooms: Desired number of rooms (best effort; capped by space).
        :param min_room_size: Minimum width and height for any resulting room, in meters.
        """
        if num_rooms < 1:
            raise ValueError(f"num_rooms must be >= 1, got {num_rooms}")
        self._num_rooms = num_rooms
        self._min_room_size = min_room_size

    def subdivide(self, footprint: Rectangle, rng: random.Random) -> Subdivision:
        """Partition ``footprint`` into rooms using ``rng`` for split positions."""
        rooms = [footprint]
        interior_walls = []

        while len(rooms) < self._num_rooms:
            index = self._pick_splittable_room(rooms)
            if index is None:
                logger.debug(
                    "stopping at %d rooms (requested %d): no room can be split at min_size %.2f",
                    len(rooms),
                    self._num_rooms,
                    self._min_room_size,
                )
                break
            target = rooms.pop(index)
            low, high, segment = self._split_room(target, rng)
            rooms.append(low)
            rooms.append(high)
            interior_walls.append(segment)

        return Subdivision(rooms=rooms, interior_walls=interior_walls)

    def _pick_splittable_room(self, rooms: list[Rectangle]) -> int | None:
        """Index of the largest room that can still be split, or None if none can."""
        best_index = None
        best_area = -1.0
        for index, room in enumerate(rooms):
            if self._can_split(room) and room.area > best_area:
                best_index = index
                best_area = room.area
        return best_index

    def _can_split(self, room: Rectangle) -> bool:
        """A room is splittable if its longer axis can yield two min-sized halves."""
        longer_extent = max(room.width, room.height)
        return longer_extent >= 2 * self._min_room_size

    def _split_room(self, room: Rectangle, rng: random.Random):
        """Split ``room`` along its longer axis at a jittered, min-size-respecting cut."""
        axis = room.longer_axis
        low_bound, high_bound = self._split_bounds(room, axis)
        center = (low_bound + high_bound) / 2.0
        half_window = _JITTER_FRACTION * (high_bound - low_bound) / 2.0
        at = rng.uniform(center - half_window, center + half_window)
        return room.split(axis, at)

    def _split_bounds(self, room: Rectangle, axis: str) -> tuple[float, float]:
        """Inclusive coordinate range on ``axis`` where a cut keeps both halves >= min."""
        if axis == "x":
            return room.x0 + self._min_room_size, room.x1 - self._min_room_size
        return room.y0 + self._min_room_size, room.y1 - self._min_room_size
