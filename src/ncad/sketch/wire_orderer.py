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

_CONNECTIVE = frozenset({"line", "arc", "bezier", "interpolated", "ellipse_arc"})


class WireOrderer:
    """Orders solved primitive entities into kernel edge descriptors."""

    def order(self, entities: list[dict], positions: dict[str, tuple[float, float]],
              radii: dict[str, float]) -> tuple[list[dict], str | None]:
        """Return ``(ordered edge descriptors, None)`` or ``([], error_message)``."""
        # Construction/reference entities (e.g. projected edges) anchor the sketch but
        # are not part of the built wire.
        entities = [e for e in entities if not e.get("construction")]
        closed = [e for e in entities if e.get("type") in ("circle", "ellipse")]
        connective = [e for e in entities if e.get("type") in _CONNECTIVE]
        if closed and connective:
            return [], "a full circle/ellipse must be the only entity in its sketch loop"
        if closed:
            if len(closed) != 1:
                return [], "a sketch loop supports a single full circle/ellipse"
            entity = closed[0]
            if entity["type"] == "circle":
                center = positions[entity["center"]]
                return [{"kind": "circle", "center": center,
                         "radius": radii.get(entity["id"], entity.get("radius", 0.0))}], None
            return [{"kind": "ellipse", "center": positions[entity["center"]],
                     "major_axis_end": positions[entity["major_axis_end"]],
                     "minor_radius": float(radii.get(entity["id"],
                                                     entity["minor_radius"]))}], None
        if not connective:
            return [], "sketch has no entities to form a loop"
        return self._order_connective(connective, positions)

    def order_open(self, entities: list[dict], positions: dict[str, tuple[float, float]],
                   radii: dict[str, float]) -> tuple[list[dict], str | None]:
        """Order an OPEN chain of lines/arcs into edge descriptors (a path, not a loop).

        Unlike ``order``, this expects exactly two degree-1 endpoints (the path ends) and
        does not close the chain or reorient it: an open path has no inside, so the CCW
        winding rule does not apply.
        """
        entities = [e for e in entities if not e.get("construction")]
        connective = [e for e in entities if e.get("type") in _CONNECTIVE]
        if not connective:
            return [], "open sketch has no line/arc entities to form a path"
        if any(e.get("type") in ("circle", "ellipse") for e in entities):
            return [], "an open sketch path cannot contain a full circle/ellipse"
        endpoints = {e["id"]: _endpoints(e) for e in connective}
        adjacency: dict[str, list[str]] = {}
        for eid, (a, b) in endpoints.items():
            adjacency.setdefault(a, []).append(eid)
            adjacency.setdefault(b, []).append(eid)
        ends = [p for p, es in adjacency.items() if len(es) == 1]
        if len(ends) != 2 or any(len(es) > 2 for es in adjacency.values()):
            return [], "open sketch entities do not form a single open path"
        by_id = {e["id"]: e for e in connective}
        start_point = ends[0]
        current_edge: str | None = adjacency[start_point][0]
        prev_point, current_point = start_point, _other_end(
            endpoints[current_edge], start_point)
        ordered: list[dict] = []
        used: set[str] = set()
        while current_edge is not None and current_edge not in used:
            used.add(current_edge)
            descriptor, err = self._descriptor(by_id[current_edge], prev_point,
                                               current_point, positions)
            if err is not None:
                return [], err
            ordered.append(descriptor)
            nxt = next((e for e in adjacency[current_point] if e != current_edge), None)
            if nxt is None:
                break
            prev_point, current_point = current_point, _other_end(
                endpoints[nxt], current_point)
            current_edge = nxt
        if len(used) != len(connective):
            return [], "open sketch entities do not form a single open path"
        return ordered, None

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
        if _signed_area(ordered) < 0.0:
            ordered = _reverse_loop(ordered)
        return ordered, None

    def _descriptor(self, edge: dict, from_point: str, to_point: str,
                    positions: dict[str, tuple[float, float]]) -> tuple[dict, str | None]:
        """One edge descriptor in traversal order from ``from_point`` to ``to_point``."""
        start = positions[from_point]
        end = positions[to_point]
        if edge["type"] == "line":
            return {"kind": "line", "points": [start, end]}, None
        if edge["type"] in ("bezier", "interpolated"):
            # The interpolated entity type maps to the geometry-level descriptor kind
            # "spline"; bezier stays "bezier". Defining points are emitted in traversal
            # order: if the walk enters from the curve's last point, reverse them so the
            # built curve direction matches the loop/path direction (as arcs do).
            kind = "bezier" if edge["type"] == "bezier" else "spline"
            point_ids = edge["points"]
            if point_ids[0] == to_point:
                point_ids = list(reversed(point_ids))
            return {"kind": kind, "points": [positions[p] for p in point_ids]}, None
        if edge["type"] == "ellipse_arc":
            return {"kind": "ellipse_arc",
                    "center": positions[edge["center"]],
                    "major_axis_end": positions[edge["major_axis_end"]],
                    "minor_radius": float(edge["minor_radius"]),
                    "points": [start, end]}, None
        center = positions[edge["center"]]
        mid, err = _arc_mid(center, positions[edge["start"]], positions[edge["end"]])
        if err is not None:
            return {}, err
        return {"kind": "arc", "points": [start, mid, end]}, None


def _signed_area(edges: list[dict]) -> float:
    """Signed shoelace area over the loop's ordered edge start points (CCW positive)."""
    # A spline bulges off the chord between its endpoints, so this endpoint-polygon area
    # only approximates the true enclosed area. It is used SOLELY to choose CCW-vs-CW
    # reorientation, and the endpoint polygon carries the same orientation sign as the real
    # curve for any non-self-intersecting loop, so it is correct for that purpose without
    # integrating the curve.
    ring = [edge["points"][0] for edge in edges]
    total = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return total / 2.0


def _reverse_loop(edges: list[dict]) -> list[dict]:
    """Reverse a loop's direction so it winds counter-clockwise (a +Z face normal).

    Each edge's point order is reversed (an arc keeps its mid point, swapping start/end),
    and the edge sequence is reversed, so the loop is traversed the other way.
    """
    reversed_edges: list[dict] = []
    for edge in reversed(edges):
        pts = list(reversed(edge["points"]))
        reversed_edges.append({**edge, "points": pts})
    return reversed_edges


def _other_end(ends: tuple[str, str], point: str) -> str:
    """The endpoint of ``ends`` that is not ``point``."""
    a, b = ends
    return b if a == point else a


def _endpoints(edge: dict) -> tuple[str, str]:
    """The two connecting point ids of an edge, in authored order.

    A spline/bezier connects only at its first and last defining point; interior
    control/through points shape the curve but are not connection nodes.
    """
    kind = edge["type"]
    if kind == "line":
        return edge["p1"], edge["p2"]
    if kind in ("arc", "ellipse_arc"):
        return edge["start"], edge["end"]
    points = edge["points"]
    return points[0], points[-1]


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
