from ncad.service.build_job import BuildJob
from ncad.service.job_store import JobStore


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


def _job(job_id, kind="build", spec="a.hocon", status="queued", created=1000.0):
    return BuildJob(id=job_id, kind=kind, spec=spec, status=status, stage="queued",
                    stages_done=0, stages_total=4, message="", result=None, error=None,
                    created_at=created, finished_at=None)


def test_add_and_get_roundtrip():
    store = JobStore(clock=FakeClock(), ttl_s=300.0, max_jobs=100)
    job = _job("j1")
    store.add(job)
    assert store.get("j1") is job


def test_get_unknown_is_none():
    store = JobStore(clock=FakeClock(), ttl_s=300.0, max_jobs=100)
    assert store.get("nope") is None


def test_inflight_coalescing_matches_same_kind_spec():
    store = JobStore(clock=FakeClock(), ttl_s=300.0, max_jobs=100)
    job = _job("j1", kind="build", spec="a.hocon")
    store.add(job)
    assert store.find_inflight("build", "a.hocon") is job
    assert store.find_inflight("build", "other.hocon") is None
    assert store.find_inflight("assemble", "a.hocon") is None


def test_terminal_job_is_not_coalesced():
    store = JobStore(clock=FakeClock(), ttl_s=300.0, max_jobs=100)
    job = _job("j1", kind="build", spec="a.hocon")
    store.add(job)
    job.status = "done"
    job.finished_at = 1001.0
    store.mark_terminal("j1")
    assert store.find_inflight("build", "a.hocon") is None
    assert store.get("j1") is job    # still retrievable until TTL


def test_ttl_eviction_of_terminal_job():
    clock = FakeClock()
    store = JobStore(clock=clock, ttl_s=300.0, max_jobs=100)
    job = _job("j1")
    store.add(job)
    job.status = "done"
    job.finished_at = clock.t
    store.mark_terminal("j1")
    clock.t += 301.0                 # advance past ttl
    assert store.get("j1") is None   # evicted on read


def test_ttl_does_not_evict_running_job():
    clock = FakeClock()
    store = JobStore(clock=clock, ttl_s=1.0, max_jobs=100)
    job = _job("j1", status="running")
    store.add(job)
    clock.t += 100.0
    assert store.get("j1") is job    # non-terminal never evicted by TTL


def test_max_jobs_cap_drops_oldest_terminal():
    clock = FakeClock()
    store = JobStore(clock=clock, ttl_s=10_000.0, max_jobs=2)
    for i in range(3):
        j = _job(f"j{i}", spec=f"s{i}.hocon", created=1000.0 + i)
        store.add(j)
        j.status = "done"
        j.finished_at = 1000.0 + i
        store.mark_terminal(f"j{i}")
    # Over cap (3 > 2): the oldest terminal (j0) is dropped.
    assert store.get("j0") is None
    assert store.get("j1") is not None
    assert store.get("j2") is not None
