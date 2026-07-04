"""The ``sketch`` feature op: turn 2D elements or a constrained entity set into a face.

Two authoring forms coexist. The primitive form (``elements``: one ``rectangle``,
``circle``, or ``polygon`` centred on the origin) is unchanged. The constrained form
(``entities`` + ``constraints``) is solved by a :class:`SketchSolver` (design section 5)
into 2D positions, ordered into a closed wire, and built as a planar face.
"""

import math
from typing import Any

from ncad.kernel.kernel import Kernel, Point2
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.sketch.sketch_solver import SketchSolver


class SketchOp:
    """Builds a planar face from a feature's sketch elements or constrained entities."""

    def __init__(self, solver: "SketchSolver | None" = None) -> None:
        """:param solver: Constraint solver for the entities form (default SlvsSolver)."""
        if solver is None:
            from ncad.sketch.slvs_solver import SlvsSolver
            solver = SlvsSolver()
        self._solver = solver

    def build(
        self, shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel
    ) -> OpResult:
        """Build a planar face from the feature's sketch elements or entities.

        :param shape_in: Ignored; a sketch originates geometry (no upstream shape).
        :param params: The feature dict (``id``, ``plane``, ``elements`` or ``entities``).
        :param provenance_in: Provenance accumulated from earlier features.
        :param kernel: Geometry backend.
        :return: An :class:`OpResult` whose shape is the face, or ``None`` + an issue.
        """
        if params.get("entities"):
            return self._build_from_entities(params, kernel)
        feature_id = params["id"]
        plane = params.get("plane", "XY")
        elements = params.get("elements", [])
        if len(elements) != 1:
            issue = BuildIssue(
                node_id=feature_id,
                message=f"sketch supports exactly one element; got {len(elements)}",
            )
            return OpResult(shape=None, provenance={}, issues=[issue])

        element = elements[0]
        kind = element.get("type")
        if kind == "rectangle":
            points = self._rectangle_points(element["w"], element["h"])
            return OpResult(shape=kernel.polygon_face(points, plane),
                            provenance={}, issues=[])
        if kind == "circle":
            diameter = element["d"] if "d" in element else element["r"] * 2.0
            return OpResult(shape=kernel.circle_face((0.0, 0.0), diameter, plane),
                            provenance={}, issues=[])
        if kind == "polygon":
            return OpResult(shape=kernel.polygon_face(self._polygon_points(element), plane),
                            provenance={}, issues=[])
        issue = BuildIssue(node_id=feature_id, message=f"unknown sketch element type: {kind!r}")
        return OpResult(shape=None, provenance={}, issues=[issue])

    def _build_from_entities(self, params: dict, kernel: Kernel) -> OpResult:
        """Solve a constrained entity set and build a face from the closed wire."""
        feature_id = params["id"]
        plane = params.get("plane", "XY")
        entities = params["entities"]
        constraints = params.get("constraints", [])
        result = self._solver.solve(entities, constraints, feature_id)
        if any(issue.level == "error" for issue in result.issues):
            return OpResult(shape=None, provenance={}, issues=result.issues)
        ring, ring_error = _order_ring(entities, result.positions)
        if ring_error is not None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=ring_error)])
        face = kernel.polygon_face(ring, plane)
        return OpResult(shape=face, provenance={}, issues=result.issues)

    @staticmethod
    def _rectangle_points(width: float, height: float) -> list[Point2]:
        """Corner ring of a ``width`` x ``height`` rectangle centred on the origin."""
        half_w, half_h = width / 2.0, height / 2.0
        return [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]

    @staticmethod
    def _polygon_points(element: dict) -> list[Point2]:
        """Point ring for a polygon: explicit ``points``, or a regular ``sides``+``r``."""
        if "points" in element:
            return [(float(x), float(y)) for x, y in element["points"]]
        sides = int(element["sides"])
        r = float(element["r"])
        return [(r * math.cos(2 * math.pi * i / sides), r * math.sin(2 * math.pi * i / sides))
                for i in range(sides)]


def _order_ring(entities: list[dict], positions: dict) -> tuple[list, str | None]:
    """Order line endpoints into a single closed loop of (u, v) points.

    Follows line connectivity: each line contributes an edge between two point ids; the
    loop is the ordered vertex sequence. Returns ``(ordered_points, None)`` on success,
    or ``([], message)`` when the lines do not form one closed loop (bucket 1.1 scope).
    """
    lines = [e for e in entities if e.get("type") == "line"]
    if not lines:
        return [], "sketch has no line entities to form a loop"
    adjacency: dict = {}
    for line in lines:
        adjacency.setdefault(line["p1"], []).append(line["p2"])
        adjacency.setdefault(line["p2"], []).append(line["p1"])
    if any(len(neighbours) != 2 for neighbours in adjacency.values()):
        return [], "sketch entities do not form a single closed loop"
    start = lines[0]["p1"]
    order = [start]
    prev, current = None, start
    while True:
        nxt = next((n for n in adjacency[current] if n != prev), None)
        if nxt is None or nxt == start:
            break
        order.append(nxt)
        prev, current = current, nxt
    if len(order) != len(adjacency):
        return [], "sketch entities do not form a single closed loop"
    return [positions[pid] for pid in order], None
