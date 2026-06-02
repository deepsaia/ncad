"""Topological validation: every room reachable from every other through doors.

Builds a room graph whose edges are doors on walls shared between two rooms, then checks
connectivity. An unreachable room means the building has no door path into it.
"""

import logging

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)

_EPSILON = 1e-6


class TopologyValidator:
    """Validates room reachability via the door graph."""

    def validate(self, spec: dict) -> list[Issue]:
        """Return topology issues for ``spec`` (empty if all rooms reachable)."""
        issues: list[Issue] = []
        for storey in spec["storeys"]:
            issues.extend(self._validate_storey(storey))
        return issues

    def _validate_storey(self, storey: dict) -> list[Issue]:
        rooms = storey["rooms"]
        if len(rooms) <= 1:
            return []
        adjacency = self._build_door_adjacency(storey)
        reachable = self._reachable_from(rooms[0]["id"], adjacency)
        return [
            Issue(
                kind="unreachable_room",
                entity_id=room["id"],
                message=f"room {room['id']!r} is not reachable through any door",
            )
            for room in rooms
            if room["id"] not in reachable
        ]

    def _build_door_adjacency(self, storey: dict) -> dict[str, set[str]]:
        """Map each room id to the room ids it shares a door-bearing wall with."""
        adjacency: dict[str, set[str]] = {room["id"]: set() for room in storey["rooms"]}
        for wall in storey["walls"]:
            if not _has_door(wall):
                continue
            touching = [
                room["id"]
                for room in storey["rooms"]
                if _wall_on_room_boundary(wall, room["polygon"])
            ]
            for i, room_a in enumerate(touching):
                for room_b in touching[i + 1 :]:
                    adjacency[room_a].add(room_b)
                    adjacency[room_b].add(room_a)
        return adjacency

    def _reachable_from(self, start: str, adjacency: dict[str, set[str]]) -> set[str]:
        seen = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        return seen


def _has_door(wall: dict) -> bool:
    return any(o["kind"] == "door" for o in wall.get("openings", []))


def _wall_on_room_boundary(wall: dict, polygon: list) -> bool:
    """True if the wall's centerline lies along one of the room polygon's edges."""
    start = tuple(wall["start"])
    end = tuple(wall["end"])
    count = len(polygon)
    for i in range(count):
        a = tuple(polygon[i])
        b = tuple(polygon[(i + 1) % count])
        if _segment_overlaps_collinear(start, end, a, b):
            return True
    return False


def _segment_overlaps_collinear(p0, p1, q0, q1) -> bool:
    """True if segment p lies collinear with edge q and overlaps it with positive length."""
    if not _collinear(p0, p1, q0) or not _collinear(p0, p1, q1):
        return False
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length_sq = dx * dx + dy * dy
    if length_sq < _EPSILON:
        return False
    t0 = ((q0[0] - p0[0]) * dx + (q0[1] - p0[1]) * dy) / length_sq
    t1 = ((q1[0] - p0[0]) * dx + (q1[1] - p0[1]) * dy) / length_sq
    low, high = sorted((t0, t1))
    overlap = min(high, 1.0) - max(low, 0.0)
    return overlap > _EPSILON


def _collinear(a, b, c) -> bool:
    cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return abs(cross) < _EPSILON
