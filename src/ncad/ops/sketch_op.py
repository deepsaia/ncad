"""The ``sketch`` feature op: turn 2D elements or a constrained entity set into a face.

Two authoring forms coexist. The primitive form (``elements``: one ``rectangle``,
``circle``, or ``polygon`` centred on the origin) is unchanged. The constrained form
(``entities`` + ``constraints``) is solved by a :class:`SketchSolver` (design section 5)
into 2D positions, ordered into a closed wire, and built as a planar face.
"""

import math
from typing import TYPE_CHECKING, Any

from ncad.kernel.kernel import Kernel, Point2
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.sketch_status import SketchStatus
from ncad.sketch.edge_projector import EdgeProjector
from ncad.sketch.entity_expander import EntityExpander
from ncad.sketch.offset_applier import OffsetApplier, OffsetError
from ncad.sketch.topology_applier import TopologyApplier, TopologyError
from ncad.sketch.transform_applier import TransformApplier, TransformError
from ncad.sketch.wire_orderer import WireOrderer

if TYPE_CHECKING:
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
        if (params.get("entities") or params.get("project")
                or params.get("transforms") or params.get("modify")):
            return self._build_from_entities(params, kernel)
        feature_id = params["id"]
        plane = params.get("plane", "XY")
        offset = float(params.get("plane_offset", 0.0))
        elements = params.get("elements", [])
        if len(elements) != 1:
            issue = BuildIssue(
                node_id=feature_id,
                message=f"sketch supports exactly one element; got {len(elements)}",
            )
            return OpResult(shape=None, provenance={}, issues=[issue])

        element = elements[0]
        kind = element.get("type")
        # A primitive element sketch has no solver: it is trivially well-constrained.
        well = SketchStatus(feature_id, "well", 0)
        if kind == "rectangle":
            points = self._rectangle_points(element["w"], element["h"])
            return OpResult(shape=kernel.polygon_face(points, plane, offset=offset),
                            provenance={}, issues=[], status_report=well)
        if kind == "circle":
            diameter = element["d"] if "d" in element else element["r"] * 2.0
            return OpResult(shape=kernel.circle_face((0.0, 0.0), diameter, plane,
                                                     offset=offset),
                            provenance={}, issues=[], status_report=well)
        if kind == "polygon":
            return OpResult(shape=kernel.polygon_face(self._polygon_points(element), plane,
                                                      offset=offset),
                            provenance={}, issues=[], status_report=well)
        issue = BuildIssue(node_id=feature_id, message=f"unknown sketch element type: {kind!r}")
        return OpResult(shape=None, provenance={}, issues=[issue])

    def _build_from_entities(self, params: dict, kernel: Kernel) -> OpResult:
        """Solve a constrained entity set and build a face from the closed wire.

        Handles reference-into-sketch (project prior edges onto the plane as fixed
        construction entities) and offset (derive real entities), then expand/solve/order.
        """
        feature_id = params["id"]
        plane = params.get("plane", "XY")
        offset = float(params.get("plane_offset", 0.0))
        entities = list(params.get("entities", []))
        projected_issue = None
        project_edges = params.get("__refs__", {}).get("project")
        if project_edges:
            descriptors = kernel.project_edges(project_edges, plane, offset=offset)
            reference_entities, degenerate = EdgeProjector().project(descriptors)
            entities = reference_entities + entities
            if degenerate and not reference_entities:
                return OpResult(shape=None, provenance={}, issues=[BuildIssue(
                    node_id=feature_id, message="sketch projected no usable geometry")])
            if degenerate:
                projected_issue = BuildIssue(
                    node_id=feature_id,
                    message=f"{degenerate} projected edge(s) were degenerate and skipped",
                    level="warning")
        try:
            entities = OffsetApplier().apply(entities)
        except OffsetError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        entities = EntityExpander().expand(entities)
        try:
            entities = TopologyApplier().apply(entities, params.get("modify", []))
        except TopologyError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        try:
            entities = TransformApplier().apply(entities, params.get("transforms", []))
        except TransformError as exc:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=str(exc))])
        constraints = params.get("constraints", [])
        result = self._solver.solve(entities, constraints, feature_id)
        issues = list(result.issues)
        if projected_issue is not None:
            issues.append(projected_issue)
        status = SketchStatus(feature_id, _short_status(result.status), result.dof,
                              result.failing_ids)
        if any(issue.level == "error" for issue in issues):
            return OpResult(shape=None, provenance={}, issues=issues,
                            status_report=status)
        if params.get("open"):
            # Open mode: emit an ordered OPEN wire (a sweep path) instead of a face.
            edges, path_error = WireOrderer().order_open(
                entities, result.positions, result.radii)
            if path_error is not None:
                return OpResult(shape=None, provenance={},
                                issues=[BuildIssue(node_id=feature_id,
                                                   message=path_error)],
                                status_report=status)
            wire = kernel.wire(edges, plane, offset=offset)
            return OpResult(shape=wire, provenance={}, issues=issues,
                            status_report=status)
        edges, ring_error = WireOrderer().order(entities, result.positions, result.radii)
        if ring_error is not None:
            return OpResult(shape=None, provenance={},
                            issues=[BuildIssue(node_id=feature_id, message=ring_error)],
                            status_report=status)
        face = kernel.wire_face(edges, plane, offset=offset)
        return OpResult(shape=face, provenance={}, issues=issues, status_report=status)

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


_SHORT_STATUS = {"well_constrained": "well", "under_constrained": "under",
                 "inconsistent": "inconsistent"}


def _short_status(status: str) -> str:
    """Map a SolveResult status to the short viewer/sidecar vocabulary.

    ``over`` and ``inconsistent`` share the solver's ``inconsistent`` status; both surface
    as ``inconsistent`` (an over-constrained sketch is a special inconsistency).
    """
    return _SHORT_STATUS.get(status, status)
