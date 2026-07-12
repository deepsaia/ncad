"""The ``defeature`` direct op: remove a simple planar face, gated by the 4.0 envelope."""

import logging
from typing import Any

from ncad.ops.build_issue import BuildIssue
from ncad.ops.direct_edit_guard import DirectEditGuard
from ncad.ops.direct_edit_runner import DirectEditRunner
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class DefeatureOp:
    """Removes a face from the running solid when the envelope allows it."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "defeature")
        # The resolved face Element (handle + attrs) arrives via the builder's __refs__ dict.
        face = params.get("__refs__", {}).get("face")
        if shape_in is None:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, "defeature has no input solid")])
        verdict = DirectEditGuard().check(kernel, shape_in, face, "defeature", params)
        if not verdict.allowed:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, verdict.reason or "defeature refused")])
        handle = face.handle
        try:
            run = DirectEditRunner().run(kernel, lambda: kernel.defeature(shape_in, handle),
                                         shape_in, "defeature")
        except Exception as exc:  # noqa: BLE001 - a KernelOpError becomes an id-attributed issue
            logger.warning("defeature failed on %s: %s", node_id, exc)
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, f"defeature failed: {exc}")])
        if not run.accepted:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, run.reason or "defeature not accepted")])
        return OpResult(shape=run.shape)
