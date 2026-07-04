"""Turn solved primitive entities into an ordered list of kernel edge descriptors.

Walks the line/arc connectivity of a sketch into a single closed loop and emits the
edge descriptors the kernel's ``wire_face`` consumes: ``line`` (two solved points),
``arc`` (start, computed mid, end), or a lone ``circle`` (center + solved radius). A
sketch that is not a single closed loop, mixes a circle with open edges, or contains a
degenerate arc is reported as an error string rather than handed to the kernel.
"""

import logging
import math

logger = logging.getLogger(__name__)

_CONNECTIVE = frozenset({"line", "arc"})


class WireOrderer:
    """Orders solved primitive entities into kernel edge descriptors."""

    def order(self, entities: list[dict], positions: dict[str, tuple[float, float]],
              radii: dict[str, float]) -> tuple[list[dict], str | None]:
        """Return ``(ordered edge descriptors, None)`` or ``([], error_message)``."""
        circles = [e for e in entities if e.get("type") == "circle"]
        connective = [e for e in entities if e.get("type") in _CONNECTIVE]
        if circles and connective:
            return [], "a circle must be the only entity in its sketch loop"
        if circles:
            if len(circles) != 1:
                return [], "a sketch loop supports a single circle"
            circle = circles[0]
            center = positions[circle["center"]]
            return [{"kind": "circle", "center": center,
                     "radius": radii.get(circle["id"], circle.get("radius", 0.0))}], None
        if not connective:
            return [], "sketch has no entities to form a loop"
        return self._order_connective(connective, positions)

    def _order_connective(self, edges: list[dict],
                          positions: dict[str, tuple[float, float]]) -> tuple[list, str | None]:
        """Walk a connected loop of lines/arcs into ordered edge descriptors."""
        endpoints = {e["id"]: _endpoints(e) for e in edges}
        adjacency: dict[str, list[str]] = {}
        for eid, (a, b) in endpoints.items():
            adjacency.setdefault(a, []).append(eid)
            adjacency.setdefault(b, []).append(eid)
        if any(len(v) != 2 for v in adjacency.values()):
            return [], "sketch entities do not form a single closed loop"

        by_id = {e["id"]: e for e in edges}
        start_edge = edges[0]
        prev_point, current_point = endpoints[start_edge["id"]]
        ordered: list[dict] = []
        used: set[str] = set()
        current_edge = start_edge["id"]
        while current_edge not in used:
            used.add(current_edge)
            descriptor, err = self._descriptor(by_id[current_edge], prev_point,
                                               current_point, positions)
            if err is not None:
                return [], err
            ordered.append(descriptor)
            nxt = next((e for e in adjacency[current_point] if e != current_edge), None)
            if nxt is None:
                break
            a, b = endpoints[nxt]
            prev_point, current_point = current_point, (b if a == current_point else a)
            current_edge = nxt
        if len(used) != len(edges):
            return [], "sketch entities do not form a single closed loop"
        return ordered, None

    def _descriptor(self, edge: dict, from_point: str, to_point: str,
                    positions: dict[str, tuple[float, float]]) -> tuple[dict, str | None]:
        """One edge descriptor in traversal order from ``from_point`` to ``to_point``."""
        start = positions[from_point]
        end = positions[to_point]
        if edge["type"] == "line":
            return {"kind": "line", "points": [start, end]}, None
        center = positions[edge["center"]]
        mid, err = _arc_mid(center, positions[edge["start"]], positions[edge["end"]])
        if err is not None:
            return {}, err
        return {"kind": "arc", "points": [start, mid, end]}, None


def _endpoints(edge: dict) -> tuple[str, str]:
    """The two connecting point ids of a line or arc, in authored order."""
    if edge["type"] == "line":
        return edge["p1"], edge["p2"]
    return edge["start"], edge["end"]


def _arc_mid(center: tuple[float, float], start: tuple[float, float],
             end: tuple[float, float]) -> tuple[tuple[float, float], str | None]:
    """Midpoint of the CCW arc start->end about ``center``; error if degenerate."""
    cx, cy = center
    sx, sy = start
    ex, ey = end
    radius = math.hypot(sx - cx, sy - cy)
    if radius < 1e-9 or (abs(sx - ex) < 1e-9 and abs(sy - ey) < 1e-9):
        return (0.0, 0.0), "degenerate arc (zero radius or coincident endpoints)"
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    while a1 <= a0:
        a1 += 2.0 * math.pi
    mid = (a0 + a1) / 2.0
    return (cx + radius * math.cos(mid), cy + radius * math.sin(mid)), None
