from concurrent.futures import Future

import pytest

from ncad.service.job_manager import JobManager, SaturatedError
from ncad.service.job_store import JobStore


class FakePool:
    """Records submissions; returns a Future the test resolves manually."""

    def __init__(self):
        self.submitted = []
        self.futures = []
        self._active = 0

    def submit(self, kind, payload, models_dir, examples_dir, progress_path):
        self.submitted.append((kind, payload))
        fut = Future()
        self.futures.append(fut)
        self._active += 1
        return fut

    def active_count(self):
        return self._active

    def shutdown(self, wait, timeout_s):
        pass


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _ids():
    seq = iter(f"job{i}" for i in range(1000))
    return lambda: next(seq)


def sync_add_future(future, callback):
    """Invoke the done-callback immediately (test stand-in for IOLoop.add_future)."""
    future.add_done_callback(callback)


def _manager(pool, store=None, max_concurrent=2, queue_max=2, tmp="/tmp"):
    store = store or JobStore(clock=Clock(), ttl_s=300.0, max_jobs=100)
    return JobManager(pool=pool, store=store, models_dir=tmp, examples_dir="",
                      jobs_dir=tmp, max_concurrent=max_concurrent, queue_max=queue_max,
                      id_factory=_ids(), clock=Clock(), add_future=sync_add_future)


def test_submit_creates_queued_job_and_submits_to_pool():
    pool = FakePool()
    mgr = _manager(pool)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    assert job.status in ("queued", "running")
    assert pool.submitted == [("build", {"spec": "a.hocon"})]


def test_done_future_finalizes_job_result():
    pool = FakePool()
    mgr = _manager(pool)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    pool.futures[0].set_result({"ok": True, "result": {"built": ["a"]}})
    assert job.status == "done"
    assert job.result == {"built": ["a"]}
    assert job.finished_at is not None


def test_failed_result_dict_finalizes_as_failed():
    pool = FakePool()
    mgr = _manager(pool)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    pool.futures[0].set_result({"ok": False, "error": "not allowed"})
    assert job.status == "failed"
    assert job.error == "not allowed"


def test_worker_exception_finalizes_as_failed():
    pool = FakePool()
    mgr = _manager(pool)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    pool.futures[0].set_exception(RuntimeError("worker died"))
    assert job.status == "failed"
    assert "worker died" in job.error


def test_coalesce_returns_existing_inflight_job():
    pool = FakePool()
    mgr = _manager(pool)
    first = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    again = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    assert again is first
    assert len(pool.submitted) == 1     # only one worker submission


def test_saturation_raises():
    pool = FakePool()
    mgr = _manager(pool, max_concurrent=1, queue_max=0)
    mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    with pytest.raises(SaturatedError):
        mgr.submit("assemble", {"spec": "b.hocon"}, coalesce_key="b.hocon")


def test_cancel_pending_future():
    pool = FakePool()
    mgr = _manager(pool)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    ok = mgr.cancel(job.id)
    assert ok is True
    assert job.status == "cancelled"


def test_finalize_deletes_progress_file(tmp_path):
    import os

    pool = FakePool()
    store = JobStore(clock=Clock(), ttl_s=300.0, max_jobs=100)
    mgr = JobManager(pool=pool, store=store, models_dir=str(tmp_path), examples_dir="",
                     jobs_dir=str(tmp_path), max_concurrent=2, queue_max=2,
                     id_factory=_ids(), clock=Clock(), add_future=sync_add_future)
    job = mgr.submit("build", {"spec": "a.hocon"}, coalesce_key="a.hocon")
    progress = tmp_path / f"{job.id}.progress.json"
    progress.write_text("{}")
    pool.futures[0].set_result({"ok": True, "result": {}})
    assert not os.path.exists(progress)   # cleaned on finalize (bounds the .jobs dir)


def test_get_logs_stage_transition_once(tmp_path, caplog):
    import logging

    pool = FakePool()
    store = JobStore(clock=Clock(), ttl_s=300.0, max_jobs=100)
    mgr = JobManager(pool=pool, store=store, models_dir=str(tmp_path), examples_dir="",
                     jobs_dir=str(tmp_path), max_concurrent=2, queue_max=2,
                     id_factory=_ids(), clock=Clock(), add_future=lambda f, c: None)
    job = mgr.submit("analyze", {"spec": "c.hocon"}, coalesce_key="c.hocon")
    (tmp_path / f"{job.id}.progress.json").write_text(
        '{"stage": "meshing", "stages_done": 1, "stages_total": 4, "message": "c - meshing"}')
    with caplog.at_level(logging.INFO, logger="ncad.service.job_manager"):
        mgr.get(job.id)   # first read: stage changes queued -> meshing, logs once
        mgr.get(job.id)   # second read: same stage, no new log
    transitions = [r for r in caplog.records if "meshing" in r.getMessage()]
    assert len(transitions) == 1


def test_get_overlays_progress_file(tmp_path):
    pool = FakePool()
    store = JobStore(clock=Clock(), ttl_s=300.0, max_jobs=100)
    mgr = JobManager(pool=pool, store=store, models_dir=str(tmp_path), examples_dir="",
                     jobs_dir=str(tmp_path), max_concurrent=2, queue_max=2,
                     id_factory=_ids(), clock=Clock(), add_future=lambda f, c: None)
    job = mgr.submit("analyze", {"spec": "c.hocon"}, coalesce_key="c.hocon")
    (tmp_path / f"{job.id}.progress.json").write_text(
        '{"stage": "meshing", "stages_done": 1, "stages_total": 4, "message": "c - meshing"}')
    fetched = mgr.get(job.id)
    assert fetched.stage == "meshing"
    assert fetched.stages_done == 1
    assert fetched.message == "c - meshing"
