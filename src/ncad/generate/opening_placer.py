"""Deterministic placement of doors and windows on assembled walls.

Doors on interior walls make every room reachable (the splits form a spanning tree, so
one door per interior wall connects all rooms). Windows go on exterior walls by a simple
spacing rule, and a single front door is placed on the first exterior wall. Openings are
parameterized by ``along`` (0..1) on the wall centerline, per design.md §1.
"""

import logging
import math

logger = logging.getLogger(__name__)

_DOOR_WIDTH = 1.0
_DOOR_HEIGHT = 2.1
_INTERIOR_DOOR_WIDTH = 0.9
_WINDOW_WIDTH = 1.2
_WINDOW_HEIGHT = 1.4
_WINDOW_SILL = 0.9
_FRONT_DOOR_ALONG = 0.15


class OpeningPlacer:
    """Places openings on walls and returns a map of wall id -> list of openings."""

    def __init__(self, window_spacing: float = 3.5) -> None:
        """:param window_spacing: Target spacing between windows on exterior walls (m)."""
        if window_spacing <= 0:
            raise ValueError(f"window_spacing must be > 0, got {window_spacing}")
        self._window_spacing = window_spacing

    def place(self, exterior_walls: list[dict], interior_walls: list[dict]) -> dict:
        """Compute openings for every wall.

        :param exterior_walls: Walls on the footprint boundary (get windows; the first
            also gets the front door).
        :param interior_walls: Walls separating rooms (each gets one centered door).
        :return: Mapping of wall ``id`` to its list of opening dicts.
        """
        openings_by_wall: dict[str, list[dict]] = {}

        for index, wall in enumerate(exterior_walls):
            openings = self._windows_for(wall)
            if index == 0:
                openings.insert(0, self._front_door(wall))
            openings_by_wall[wall["id"]] = openings

        for wall in interior_walls:
            openings_by_wall[wall["id"]] = [self._interior_door(wall)]

        return openings_by_wall

    def _windows_for(self, wall: dict) -> list[dict]:
        """Evenly spaced windows along ``wall``, count = floor(length / spacing)."""
        count = int(_wall_length(wall) // self._window_spacing)
        windows = []
        for i in range(count):
            along = (i + 1) / (count + 1)
            windows.append(
                {
                    "id": f"{wall['id']}_win_{i}",
                    "kind": "window",
                    "along": along,
                    "width": _WINDOW_WIDTH,
                    "height": _WINDOW_HEIGHT,
                    "sill": _WINDOW_SILL,
                }
            )
        return windows

    def _front_door(self, wall: dict) -> dict:
        return {
            "id": f"{wall['id']}_door",
            "kind": "door",
            "along": _FRONT_DOOR_ALONG,
            "width": _DOOR_WIDTH,
            "height": _DOOR_HEIGHT,
            "sill": 0.0,
        }

    def _interior_door(self, wall: dict) -> dict:
        return {
            "id": f"{wall['id']}_door",
            "kind": "door",
            "along": 0.5,
            "width": _INTERIOR_DOOR_WIDTH,
            "height": _DOOR_HEIGHT,
            "sill": 0.0,
        }


def _wall_length(wall: dict) -> float:
    """Euclidean length of a wall from its start/end centerline points."""
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return math.hypot(x1 - x0, y1 - y0)
