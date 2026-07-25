"""A lazily-created spawn ProcessPoolExecutor for CPU-bound geometry/FEA builds.

Uses the ``spawn`` start method deliberately (matching guarded_runner.py) so each worker gets a
clean interpreter and does not inherit the parent's OCCT/gmsh global state. Created on first submit
so ``ncad serve`` boots fast and pays the OCP-import cost only when a build is actually requested.
Tracks live futures for admission control. One class.
"""

import logging
import signal
from concurrent.futures import Future, ProcessPoolExecutor
from multiprocessing import get_context

from ncad.service.build_worker import run_build

logger = logging.getLogger(__name__)


def _ignore_sigint() -> None:
    """Worker initializer: ignore SIGINT so Ctrl+C is handled ONLY by the parent process.

    Spawn workers otherwise inherit the parent's SIGINT and each dump a KeyboardInterrupt traceback
    on Ctrl+C; ignoring it here lets the parent drain the pool cleanly and terminate them.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class BuildPool:
    """Owns a spawn process pool; submits run_build tasks and tracks in-flight work."""

    def __init__(self, max_workers: int) -> None:
        """:param max_workers: worker-process count (see ServiceConfig.worker_default)."""
        self._max_workers = max_workers
        self._pool: ProcessPoolExecutor | None = None
        self._live: set[Future] = set()

    def is_started(self) -> bool:
        """Whether the underlying pool has been created (first submit)."""
        return self._pool is not None

    def active_count(self) -> int:
        """Number of submitted futures not yet finished (for admission control)."""
        return sum(1 for f in self._live if not f.done())

    def submit(self, kind: str, payload: dict, models_dir: str, examples_dir: str,
               progress_path: str) -> Future:
        """Submit a build to the pool (creating it on first use); return its Future."""
        if self._pool is None:
            self._pool = ProcessPoolExecutor(
                max_workers=self._max_workers, mp_context=get_context("spawn"),
                initializer=_ignore_sigint)
            logger.info("build pool started (spawn, %d workers)", self._max_workers)
        future = self._pool.submit(
            run_build, kind, payload, models_dir, examples_dir, progress_path)
        self._live.add(future)
        future.add_done_callback(self._live.discard)
        return future

    def shutdown(self, wait: bool, timeout_s: float) -> None:
        """Shut the pool down; past ``timeout_s`` kill workers so shutdown always returns.

        ``timeout_s`` is accepted for a single shutdown seam; the actual drain bound is enforced by
        the caller (NcadService) which runs this under its own timeout, since
        ProcessPoolExecutor.shutdown takes no timeout argument.
        """
        if self._pool is None:
            return
        pool, self._pool = self._pool, None
        try:
            pool.shutdown(wait=wait, cancel_futures=True)
        except Exception:  # noqa: BLE001 - shutdown must not raise to the caller
            logger.warning("build pool shutdown raised; workers may be force-killed")
        self._live.clear()
