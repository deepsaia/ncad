"""Run a direct-edit kernel op and verify the result with the 4.0 three-tier oracle.

BRepCheck reports invalid geometry as valid 37% of the time (4.0 envelope), so a direct op's
result is accepted only if THREE independent tiers agree: the kernel validity gate (already
applied inside the _robust-wrapped op), an independent sanity check (finite positive volume,
sane face count), and the op's intent (the expected topological/volume delta). A valid-but-wrong
result is rejected, not shipped. Runs in-process; a subprocess seam is reserved for foreign
input (4.3) but unused now (clean geometry showed no hangs).
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """The verified outcome of a direct-edit op."""

    shape: Any
    accepted: bool
    reason: str | None = None


class DirectEditRunner:
    """Runs a direct-edit kernel call and accepts it only if the oracle agrees."""

    def run(self, kernel: Any, kernel_call: Callable[[], Any], before: Any, op: str,
            subprocess: bool = False, guarded_spec: dict | None = None) -> RunResult:
        """Run ``kernel_call`` and verify its result.

        When ``subprocess`` and a ``guarded_spec`` are given, run the op in a CHILD PROCESS (via
        the 4.0 GuardedRunner) so an OCCT hang/segfault on untrusted imported geometry is isolated,
        then verify the re-imported result with the same three-tier oracle. Authored geometry runs
        in-process (the spike measured no hangs there).
        """
        if subprocess and guarded_spec is not None:
            after = self._run_guarded(kernel, before, guarded_spec)
            if after is None:
                return RunResult(None, False, guarded_spec.get(
                    "failure", f"guarded {op} timed out or crashed on imported body"))
        else:
            after = kernel_call()
        if after is None:
            return RunResult(None, False, "op produced no shape")
        if not self._sanity(kernel, after):
            return RunResult(after, False, "result failed independent sanity check")
        intent_ok, reason = self._intent(kernel, before, after, op)
        if not intent_ok:
            return RunResult(after, False, reason)
        return RunResult(after, True)

    def _run_guarded(self, kernel: Any, before: Any, spec: dict) -> Any:
        # Serialize the input to a temp STEP, run the probe in a child with a wall-clock timeout,
        # re-import the result. The op stays IO-free; the runner owns the serialize round-trip.
        import os
        import tempfile

        from ncad.kernel.guarded_runner import GuardedRunner
        from ncad.ops.guarded_direct_probe import guarded_offset_probe

        if spec.get("kind") != "offset":
            # Only whole-solid offset is subprocess-guarded in this bucket (no face to re-resolve
            # across the process boundary); other ops run in-process, still oracle-verified.
            return None
        in_fd, in_path = tempfile.mkstemp(suffix=".step")
        out_fd, out_path = tempfile.mkstemp(suffix=".step")
        os.close(in_fd)
        os.close(out_fd)
        try:
            kernel.export(before, in_path)
            result = GuardedRunner(timeout_s=spec.get("timeout_s", 30.0)).run(
                guarded_offset_probe, in_path, spec["distance"], out_path)
            if result.outcome != "ok":
                logger.warning("guarded offset on imported body: %s", result.outcome)
                return None
            return kernel.import_solid(out_path)
        finally:
            for path in (in_path, out_path):
                if os.path.exists(path):
                    os.unlink(path)

    def _sanity(self, kernel: Any, shape: Any) -> bool:
        # Independent of BRepCheck: finite positive volume and at least one face.
        volume = kernel.volume(shape)
        if not (volume > 0.0 and volume < 1e15):
            return False
        faces = [d for d in kernel.describe_elements(shape) if d["kind"] == "face"]
        return len(faces) >= 1

    def _intent(self, kernel: Any, before: Any, after: Any, op: str) -> tuple[bool, str | None]:
        before_v = kernel.volume(before)
        after_v = kernel.volume(after)
        if op == "defeature":
            # Removing a face should change the solid (volume moves; face count does not grow).
            before_f = len([d for d in kernel.describe_elements(before) if d["kind"] == "face"])
            after_f = len([d for d in kernel.describe_elements(after) if d["kind"] == "face"])
            if abs(after_v - before_v) <= 1e-9 and after_f >= before_f:
                return (False, "defeature made no change (silent no-op)")
            return (True, None)
        if op == "offset":
            if abs(after_v - before_v) <= 1e-9:
                return (False, "offset made no change")
            return (True, None)
        if op == "move_face":
            # Volume must move; sanity already rejected empty/degenerate results.
            if abs(after_v - before_v) <= 1e-9:
                return (False, "move_face made no change")
            return (True, None)
        return (False, f"no intent rule for direct op {op!r}")
