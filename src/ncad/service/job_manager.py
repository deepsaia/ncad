"""Coordinates build jobs: coalesce, admission-cap, submit to the pool, and finalize on the loop.

The one collaborator handlers talk to. ``submit`` dedups an identical in-flight (kind, spec),
enforces the concurrency + queue cap (raising SaturatedError -> 503), creates a BuildJob, submits
run_build to the pool, and wires the Future's completion back onto the IOLoop (via the injected
``add_future``) so the job is finalized on the loop thread with no locking. ``arun_direct`` awaits
a build without tracking a job (for byte downloads / live checks). One class.
"""

import asyncio
import json
import logging
import os
from collections.abc import Callable
from concurrent.futures import Future

from ncad.service.build_job import BuildJob
from ncad.service.job_store import JobStore

logger = logging.getLogger(__name__)


class SaturatedError(Exception):
    """Raised by submit/run_direct when the pool + queue are full; the handler maps it to 503."""


class JobManager:
    """Submits builds to the pool, tracks them in the store, and finalizes them on the loop."""

    def __init__(self, pool, store: JobStore, models_dir: str, examples_dir: str,
                 jobs_dir: str, max_concurrent: int, queue_max: int,
                 id_factory: Callable[[], str], clock: Callable[[], float],
                 add_future: Callable[[Future, Callable], None]) -> None:
        """:param pool: a BuildPool (or same-surface fake).
        :param add_future: schedules the done-callback on the IOLoop (IOLoop.add_future in prod).
        """
        self._pool = pool
        self._store = store
        self._models_dir = models_dir
        self._examples_dir = examples_dir
        self._jobs_dir = jobs_dir
        self._max_concurrent = max_concurrent
        self._queue_max = queue_max
        self._new_id = id_factory
        self._clock = clock
        self._add_future = add_future

    def submit(self, kind: str, payload: dict, coalesce_key: str | None) -> BuildJob:
        """Coalesce or create+submit a job; raise SaturatedError when the pool + queue are full."""
        if coalesce_key is not None:
            existing = self._store.find_inflight(kind, coalesce_key)
            if existing is not None:
                return existing
        self._admit()
        job = BuildJob(id=self._new_id(), kind=kind, spec=coalesce_key or "",
                       status="queued", stage="queued", stages_done=0, stages_total=0,
                       message="queued", result=None, error=None,
                       created_at=self._clock(), finished_at=None)
        self._store.add(job)
        progress_path = os.path.join(self._jobs_dir, f"{job.id}.progress.json")
        future = self._pool.submit(
            kind, payload, self._models_dir, self._examples_dir, progress_path)
        job.status = "running"
        logger.info("job %s accepted: %s %s", job.id, kind, coalesce_key or "")
        self._add_future(future, lambda f: self._finalize(job, f))
        return job

    async def arun_direct(self, kind: str, payload: dict) -> dict:
        """Run a build in the pool and await its result WITHOUT tracking a job (bytes/live checks).

        Same admission cap as submit; returns the worker's ``{"ok", "result"|"error"}`` dict.
        """
        self._admit()
        future = self._pool.submit(kind, payload, self._models_dir, self._examples_dir,
                                   os.path.join(self._jobs_dir, "direct.progress.json"))
        return await asyncio.wrap_future(future)

    def get(self, job_id: str) -> BuildJob | None:
        """Return the job with the latest progress-file fields overlaid (None if unknown)."""
        job = self._store.get(job_id)
        if job is None:
            return None
        if job.status == "running":
            self._overlay_progress(job)
        return job

    def cancel(self, job_id: str) -> bool:
        """Cancel a job's future; mark it cancelled. Returns whether it was known + cancellable."""
        job = self._store.get(job_id)
        if job is None or job.status not in ("queued", "running"):
            return False
        job.status = "cancelled"
        job.error = "cancelled by client"
        job.finished_at = self._clock()
        self._store.mark_terminal(job.id)
        self._delete_progress(job.id)
        return True

    def shutdown(self, timeout_s: float) -> None:
        """Drain + shut the pool down (bounded by ``timeout_s``)."""
        self._pool.shutdown(wait=True, timeout_s=timeout_s)

    def _admit(self) -> None:
        """Raise SaturatedError when the pool + queue are at their bound."""
        if self._pool.active_count() >= self._max_concurrent + self._queue_max:
            raise SaturatedError("server busy: too many builds in flight")

    def _delete_progress(self, job_id: str) -> None:
        """Remove a job's progress file so <out>/.jobs/ does not accumulate (best-effort)."""
        try:
            os.remove(os.path.join(self._jobs_dir, f"{job_id}.progress.json"))
        except OSError:
            pass

    def _finalize(self, job: BuildJob, future: Future) -> None:
        """Set the job's terminal state from the Future's result/exception (runs on the loop)."""
        if job.status == "cancelled":
            self._delete_progress(job.id)
            return
        job.finished_at = self._clock()
        elapsed = job.finished_at - job.created_at
        try:
            out = future.result()
        except Exception as exc:  # noqa: BLE001 - a died worker surfaces here
            job.status = "failed"
            job.error = f"build process died: {exc}"
            logger.warning("job %s failed after %.1fs: %s", job.id, elapsed, job.error)
            self._store.mark_terminal(job.id)
            self._delete_progress(job.id)
            return
        if out.get("ok"):
            job.status = "done"
            job.result = out.get("result")
            job.stage = "done"
            logger.info("job %s %s done in %.1fs", job.id, job.kind, elapsed)
        else:
            job.status = "failed"
            job.error = out.get("error", "unknown build error")
            logger.warning("job %s %s failed after %.1fs: %s",
                           job.id, job.kind, elapsed, job.error)
        self._store.mark_terminal(job.id)
        self._delete_progress(job.id)

    def _overlay_progress(self, job: BuildJob) -> None:
        """Merge the worker's progress-file fields onto a running job (best-effort).

        Logs each stage TRANSITION at INFO so the ``ncad serve`` terminal shows build progress
        (e.g. "job abc123 analyze: solving (CalculiX) [3/4]"); only on change, not every poll.
        """
        path = os.path.join(self._jobs_dir, f"{job.id}.progress.json")
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return
        new_stage = data.get("stage", job.stage)
        if new_stage != job.stage:
            logger.info("job %s %s: %s [%s/%s]", job.id, job.kind, new_stage,
                        data.get("stages_done", 0), data.get("stages_total", 0))
        job.stage = new_stage
        job.stages_done = data.get("stages_done", job.stages_done)
        job.stages_total = data.get("stages_total", job.stages_total)
        job.message = data.get("message", job.message)
