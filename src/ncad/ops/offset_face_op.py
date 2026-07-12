"""The ``offset`` direct op: whole-solid offset/thicken, gated by the 4.0 envelope.

Per-face offset is a documented OCCT weakness (out of scope); this offsets the whole solid.
Outward (positive) is envelope GREEN; inward is refused when it would exceed the wall.
"""

import logging
from typing import Any

from ncad.ops.build_issue import BuildIssue
from ncad.ops.direct_edit_guard import DirectEditGuard
from ncad.ops.direct_edit_runner import DirectEditRunner
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class OffsetFaceOp:
    """Offsets the whole running solid by a distance when the envelope allows it."""

    def build(self, shape_in: Any, params: dict, provenance_in: dict, kernel: Any) -> OpResult:
        node_id = params.get("id", "offset")
        if shape_in is None:
            return OpResult(shape=None, issues=[BuildIssue(node_id, "offset has no input solid")])
        distance = float(params.get("distance", 0.0))
        verdict = DirectEditGuard().check(kernel, shape_in, None, "offset", params)
        if not verdict.allowed:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, verdict.reason or "offset refused")])
        # A body whose part tree includes an import is foreign geometry: run the op subprocess-
        # guarded (hang/segfault isolation). Authored geometry runs in-process (no hangs measured).
        imported = bool(params.get("__imported__"))
        guarded_spec = {"kind": "offset", "distance": distance} if imported else None
        try:
            run = DirectEditRunner().run(kernel, lambda: kernel.offset_solid(shape_in, distance),
                                         shape_in, "offset", subprocess=imported,
                                         guarded_spec=guarded_spec)
        except Exception as exc:  # noqa: BLE001 - a KernelOpError becomes an id-attributed issue
            logger.warning("offset failed on %s: %s", node_id, exc)
            return OpResult(shape=None, issues=[BuildIssue(node_id, f"offset failed: {exc}")])
        if not run.accepted:
            return OpResult(shape=None,
                            issues=[BuildIssue(node_id, run.reason or "offset not accepted")])
        return OpResult(shape=run.shape)
