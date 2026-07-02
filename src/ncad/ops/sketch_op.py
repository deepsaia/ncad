"""The ``sketch`` feature op: turn 2D elements into a planar face.

Bucket 0.1 supports a single ``rectangle`` element, centred on the plane origin. The
element vocabulary (circle, polygon, constraints) grows in Phase 1.
"""

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
        if len(elements) != 1 or elements[0].get("type") != "rectangle":
            kinds = [element.get("type") for element in elements]
            issue = BuildIssue(
                node_id=feature_id,
                message=f"sketch supports exactly one rectangle element; got {kinds}",
            )
            return OpResult(shape=None, provenance=dict(provenance_in), issues=[issue])

        element = elements[0]
        points = self._rectangle_points(element["w"], element["h"])
        face = kernel.polygon_face(points, plane)
        provenance = dict(provenance_in)
        provenance[feature_id] = "sketch"
        return OpResult(shape=face, provenance=provenance, issues=[])

    @staticmethod
    def _rectangle_points(width: float, height: float) -> list[Point2]:
        """Corner ring of a ``width`` x ``height`` rectangle centred on the origin."""
        half_w, half_h = width / 2.0, height / 2.0
        return [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
