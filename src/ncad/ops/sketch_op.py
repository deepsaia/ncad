"""The ``sketch`` feature op: turn a 2D element into a planar face.

Supports one ``rectangle``, ``circle``, or ``polygon`` element, centred on the plane
origin. The element vocabulary (arcs, splines, constraints) grows in Phase 1.
"""

import math
from typing import Any

from ncad.kernel.kernel import Kernel, Point2
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


class SketchOp:
    """Builds a planar face from a feature's sketch elements."""

    def build(
        self, shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel
    ) -> OpResult:
        """Build a planar face from the feature's sketch elements.

        :param shape_in: Ignored; a sketch originates geometry (no upstream shape).
        :param params: The feature dict (``id``, ``plane``, ``elements``).
        :param provenance_in: Provenance accumulated from earlier features.
        :param kernel: Geometry backend.
        :return: An :class:`OpResult` whose shape is the face, or ``None`` + an issue.
        """
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
