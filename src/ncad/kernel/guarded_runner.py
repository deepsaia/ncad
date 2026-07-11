"""Run a callable in a child process with a wall-clock timeout.

Direct-edit OCCT operations can hang indefinitely (OCCT #33561) or segfault; neither can be
caught by a try/except in-process, and Python signal.alarm cannot reliably interrupt a
C-extension busy loop. Running each attempt in a child process makes a hang recoverable (join
with a timeout, then terminate) and a crash observable (the parent reads the child exit code).
Phase 4.2's production direct-edit ops wrap every kernel direct-edit call in this so a kernel
fault never takes down ncad.

CONSTRAINT: the callable and its arguments cross a process boundary, so they must be
picklable. Pass a top-level function plus simple args (file paths, indices, floats). Do NOT
pass closures, lambdas, or live kernel/OCP handles; a probe re-imports its solid from a STEP
path inside the child instead.
"""

import multiprocessing as mp
import queue as queue_mod
import time
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing.queues import Queue
from typing import Any

# After the child exits, its result may still be in the queue's feeder thread (not yet flushed
# to the pipe), so a blocking drain with this timeout is more reliable than Queue.empty(), which
# can spuriously report empty and misclassify a returned value as a crash.
_DRAIN_TIMEOUT_S = 5.0


@dataclass
class GuardedResult:
    """The outcome of one guarded run.

    ``outcome`` is one of ``"ok"``, ``"timeout"``, ``"crashed"``, ``"raised"``. ``value`` is
    the callable's return value when ``outcome == "ok"`` (else ``None``); ``error`` is the
    exception repr when ``outcome == "raised"`` (else ``None``); ``elapsed_s`` is wall time.
    """

    outcome: str
    value: Any
    error: str | None
    elapsed_s: float


def _child_entry(queue: Queue, func: Callable[..., Any], args: tuple[Any, ...]) -> None:
    """Child-process entry point: run ``func`` and push ("ok", value) or ("raised", repr)."""
    try:
        result = func(*args)
        queue.put(("ok", result))
    except BaseException as exc:  # noqa: BLE001 - the child reports ANY failure back to the parent, then exits
        queue.put(("raised", repr(exc)))


class GuardedRunner:
    """Run one callable in a child process, classifying hang/crash/raise/ok."""

    def __init__(self, timeout_s: float) -> None:
        self._timeout_s = timeout_s

    def run(self, func: Callable[..., Any], *args: Any) -> GuardedResult:
        # A fresh context per run keeps the child independent; "spawn" avoids inheriting the
        # parent's OCCT global state (fork would copy a possibly-dirty kernel heap).
        ctx = mp.get_context("spawn")
        queue: Queue = ctx.Queue()
        process = ctx.Process(target=_child_entry, args=(queue, func, args))
        start = time.monotonic()
        process.start()
        process.join(self._timeout_s)
        elapsed = time.monotonic() - start

        if process.is_alive():
            # Still running past the deadline: a hang. Kill the child and record a timeout.
            process.terminate()
            process.join()
            return GuardedResult("timeout", None, None, elapsed)

        # The child finished. If it reported a message, it either returned or raised; a blocking
        # drain (not Queue.empty()) tolerates a not-yet-flushed payload. Empty after the drain
        # timeout means the child died without reporting (segfault / os._exit) -> crashed.
        try:
            tag, payload = queue.get(timeout=_DRAIN_TIMEOUT_S)
        except queue_mod.Empty:
            return GuardedResult("crashed", None, None, elapsed)
        if tag == "ok":
            return GuardedResult("ok", payload, None, elapsed)
        return GuardedResult("raised", None, str(payload), elapsed)
