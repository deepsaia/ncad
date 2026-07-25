"""In-memory registry of build jobs: id lookup, TTL eviction, count cap, and a coalescing index.

Runs entirely on the Tornado IOLoop thread (single-threaded access), so no locking is needed. A
finished job is retained for ``ttl_s`` so a late poll still sees its result, then evicted; the
store is also capped at ``max_jobs`` (oldest terminal jobs dropped first). The coalescing index
maps a live ``(kind, spec)`` to its job so an identical in-flight submit reuses it. One class.
"""

import logging
from collections.abc import Callable

from ncad.service.build_job import BuildJob

logger = logging.getLogger(__name__)

_TERMINAL = ("done", "failed", "cancelled")


class JobStore:
    """A TTL-evicting, count-capped in-memory map of job id -> BuildJob with coalescing."""

    def __init__(self, clock: Callable[[], float], ttl_s: float, max_jobs: int) -> None:
        """:param clock: monotonic-ish seconds source (injected for testability).
        :param ttl_s: seconds a terminal job is retained before eviction.
        :param max_jobs: hard cap on retained jobs; oldest terminal jobs are dropped past it.
        """
        self._clock = clock
        self._ttl_s = ttl_s
        self._max_jobs = max_jobs
        self._jobs: dict[str, BuildJob] = {}
        self._inflight: dict[tuple[str, str], str] = {}

    def add(self, job: BuildJob) -> None:
        """Record ``job`` by id and index it for coalescing while it is non-terminal."""
        self._jobs[job.id] = job
        if job.status not in _TERMINAL:
            self._inflight[(job.kind, job.spec)] = job.id

    def get(self, job_id: str) -> BuildJob | None:
        """Return the job, evicting expired terminal jobs first; None if unknown/evicted."""
        self._evict()
        return self._jobs.get(job_id)

    def find_inflight(self, kind: str, spec: str) -> BuildJob | None:
        """Return a non-terminal job matching ``(kind, spec)`` for coalescing, else None."""
        job_id = self._inflight.get((kind, spec))
        if job_id is None:
            return None
        job = self._jobs.get(job_id)
        if job is None or job.status in _TERMINAL:
            self._inflight.pop((kind, spec), None)
            return None
        return job

    def mark_terminal(self, job_id: str) -> None:
        """Drop a job's coalescing index entry once it has reached a terminal status."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        self._inflight.pop((job.kind, job.spec), None)

    def all_jobs(self) -> list[BuildJob]:
        """Every retained job (for tests + eviction bookkeeping)."""
        return list(self._jobs.values())

    def _evict(self) -> None:
        """Remove terminal jobs older than the TTL, then enforce the count cap (oldest first)."""
        now = self._clock()
        expired = [j.id for j in self._jobs.values()
                   if j.status in _TERMINAL and j.finished_at is not None
                   and now - j.finished_at > self._ttl_s]
        for job_id in expired:
            self._drop(job_id)
        if len(self._jobs) > self._max_jobs:
            terminal = sorted(
                (j for j in self._jobs.values() if j.status in _TERMINAL),
                key=lambda j: j.finished_at or j.created_at)
            overflow = len(self._jobs) - self._max_jobs
            for job in terminal[:overflow]:
                self._drop(job.id)

    def _drop(self, job_id: str) -> None:
        """Remove a job from both the id map and the coalescing index."""
        job = self._jobs.pop(job_id, None)
        if job is not None:
            self._inflight.pop((job.kind, job.spec), None)
