"""The ``relate`` direct op: apply a one-shot planar relation by moving a body (design 3).

Reads a reference planar face (fixed) and a moving planar face (on the body to move), computes
the rigid transform that satisfies the relation once (RelationalSolver), and applies it to the
moving body via kernel.transform. Planar relations only (parallel/coplanar/perpendicular/
symmetric); non-planar elements are refused. No maintenance/DoF (that is Phase 5).
"""

import logging
from typing import Any

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
from ncad.ops.build_issue import BuildIssue
from ncad.ops.op_result import OpResult
from ncad.ops.relational_solver import RelationalSolver

logger = logging.getLogger(__name__)

_PLANAR_NAMES = frozenset({"plane", None})


class RelationalEditOp:
    """Moves the running body so its face satisfies a one-shot relation with a reference face."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "relate")
        relation = params.get("relation", "")
        refs = params.get("__refs__", {})
        reference = refs.get("reference")
        moving = refs.get("moving")
        if shape_in is None:
            return OpResult(shape=None, issues=[BuildIssue(node_id, "relate has no input solid")])
        if reference is None or moving is None:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "relate needs reference and moving faces")])
        transform = self._solve(relation, reference, moving)
        if isinstance(transform, str):
            return OpResult(shape=None, issues=[BuildIssue(node_id, transform)])
        if transform is None:
            # Already satisfied: leave the body as is.
            return OpResult(shape=shape_in)
        # moving_body names ONE body of a multibody running shape to move; the rest pass through
        # unchanged (their ids and provenance survive). Absent it, the whole running solid moves
        # (single-body behavior, unchanged).
        moving_body = params.get("moving_body")
        if moving_body is not None:
            return self._move_one_body(shape_in, moving_body, transform, node_id, kernel)
        try:
            moved = kernel.transform(shape_in, move=transform["move"], rotate=transform["rotate"])
        except Exception as exc:  # noqa: BLE001 - a KernelOpError becomes an id-attributed issue
            logger.warning("relate transform failed on %s: %s", node_id, exc)
            return OpResult(shape=None, issues=[BuildIssue(node_id, f"relate failed: {exc}")])
        if moved is None or kernel.volume(moved) <= 0.0:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "relate produced a degenerate solid")])
        return OpResult(shape=moved)

    def _move_one_body(self, shape_in: Any, moving_body: str, transform: dict,
                       node_id: str, kernel: Any) -> OpResult:
        """Apply ``transform`` to just ``moving_body`` of a multibody running shape."""
        if not isinstance(shape_in, BodySet):
            return OpResult(shape=None, issues=[BuildIssue(
                node_id, "relate moving_body needs a multibody running shape")])
        try:
            target = shape_in.by_id(moving_body)
        except KeyError:
            return OpResult(shape=None, issues=[BuildIssue(
                node_id, f"relate moving_body references unknown body id {moving_body!r}")])
        try:
            moved = kernel.transform(target.shape, move=transform["move"],
                                     rotate=transform["rotate"])
        except Exception as exc:  # noqa: BLE001 - a KernelOpError becomes an id-attributed issue
            logger.warning("relate transform failed on %s: %s", node_id, exc)
            return OpResult(shape=None, issues=[BuildIssue(node_id, f"relate failed: {exc}")])
        if moved is None or kernel.volume(moved) <= 0.0:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "relate produced a degenerate solid")])
        # Rebuild the BodySet with the moved body in place; every other body keeps its id +
        # provenance (a body is born once, never re-minted by a later move).
        rebuilt = [Body(id=b.id, kind=b.kind, shape=(moved if b.id == moving_body else b.shape),
                        created_by=b.created_by) for b in shape_in.bodies]
        return OpResult(shape=BodySet(rebuilt))

    def _solve(self, relation: str, reference: Any, moving: Any) -> dict | None | str:
        """Return a transform dict, None (already satisfied), or a refusal-reason string."""
        if relation in ("parallel", "coplanar", "perpendicular", "symmetric"):
            ref_frame = self._planar_frame(reference)
            moving_frame = self._planar_frame(moving)
            if ref_frame is None or moving_frame is None:
                return "relate refused: non-planar face"
            return RelationalSolver().solve(relation, ref_frame, moving_frame)
        if relation == "coaxial":
            ref_axis = self._axis_frame(reference)
            moving_axis = self._axis_frame(moving)
            if ref_axis is None or moving_axis is None:
                return "coaxial refused: needs two cylindrical faces"
            return RelationalSolver().solve("coaxial", ref_axis, moving_axis)
        if relation == "tangent":
            ref_axis = self._axis_frame(reference)
            radius = self._radius(reference)
            moving_plane = self._planar_frame(moving)
            if ref_axis is None or radius is None:
                return "tangent refused: reference must be a cylinder"
            if moving_plane is None:
                return "tangent refused: moving face must be planar"
            return RelationalSolver().solve("tangent", ref_axis, moving_plane, radius=radius)
        return f"relate refused: unknown relation {relation!r}"

    def _planar_frame(self, element: Any) -> tuple | None:
        attrs = getattr(element, "attrs", None)
        if attrs is None:
            return None
        geom_type = attrs.get("geom_type") or attrs.get("type")
        if geom_type not in _PLANAR_NAMES:
            return None
        normal, center = attrs.get("normal"), attrs.get("center")
        if normal is None or center is None:
            return None
        return (tuple(normal), tuple(center))

    def _axis_frame(self, element: Any) -> tuple | None:
        attrs = getattr(element, "attrs", None)
        if attrs is None:
            return None
        loc, direction = attrs.get("axis_location"), attrs.get("axis_direction")
        if loc is None or direction is None:
            return None
        return (tuple(loc), tuple(direction))

    def _radius(self, element: Any) -> float | None:
        attrs = getattr(element, "attrs", None)
        if attrs is None:
            return None
        radius = attrs.get("radius")
        return float(radius) if radius is not None else None
