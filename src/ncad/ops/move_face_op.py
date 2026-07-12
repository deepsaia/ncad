"""The ``move_face`` direct op: push a planar face along its normal, gated by the 4.0 envelope.

YELLOW in the envelope: allowed only on simple planar targets with planar neighbours, guarded and
oracle-verified (the fuse/cut synthesis goes valid-but-empty on complex/blended solids).
"""

import logging
from typing import Any

from ncad.ops.build_issue import BuildIssue
from ncad.ops.direct_edit_guard import DirectEditGuard
from ncad.ops.direct_edit_runner import DirectEditRunner
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class MoveFaceOp:
    """Moves a planar face of the running solid along its normal when the envelope allows it."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "move_face")
        face = params.get("__refs__", {}).get("face")
        if shape_in is None:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "move_face has no input solid")])
        distance = float(params.get("distance", 0.0))
        verdict = DirectEditGuard().check(kernel, shape_in, face, "move_face", params)
        if not verdict.allowed:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, verdict.reason or "move_face refused")])
        handle = face.handle
        try:
            run = DirectEditRunner().run(
                kernel, lambda: kernel.move_face(shape_in, handle, distance), shape_in,
                "move_face")
        except Exception as exc:  # noqa: BLE001 - a KernelOpError becomes an id-attributed issue
            logger.warning("move_face failed on %s: %s", node_id, exc)
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, f"move_face failed: {exc}")])
        if not run.accepted:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, run.reason or "move_face not accepted")])
        return OpResult(shape=run.shape)
