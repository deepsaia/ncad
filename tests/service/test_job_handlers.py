import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from ncad.service.api_router import ApiRouter
from ncad.service.build_job import BuildJob
from ncad.service.job_manager import JobManager
from ncad.service.job_store import JobStore


class _Clock:
    def __call__(self):
        return 1000.0


class _NoPool:
    def active_count(self):
        return 0

    def shutdown(self, wait, timeout_s):
        pass


def _make_app():
    store = JobStore(clock=_Clock(), ttl_s=300.0, max_jobs=100)
    done = BuildJob(id="done1", kind="build", spec="a.hocon", status="done", stage="done",
                    stages_done=2, stages_total=2, message="", result={"built": ["a"]},
                    error=None, created_at=1000.0, finished_at=1001.0)
    running = BuildJob(id="run1", kind="analyze", spec="c.hocon", status="running",
                       stage="meshing", stages_done=1, stages_total=4, message="c - meshing",
                       result=None, error=None, created_at=1000.0, finished_at=None)
    store.add(done)
    store.add(running)
    mgr = JobManager(pool=_NoPool(), store=store, models_dir="/tmp", examples_dir="",
                     jobs_dir="/tmp", max_concurrent=2, queue_max=2,
                     id_factory=lambda: "x", clock=_Clock(), add_future=lambda f, c: None)
    deps = {"catalog": None, "spec_catalog": None, "build_service": None, "page": None,
            "dev": False, "boot_id": "b", "job_manager": mgr, "config": None}
    return Application(ApiRouter().rules(deps))


class JobHandlerTest(AsyncHTTPTestCase):
    def get_app(self):
        return _make_app()

    def test_done_job_status(self):
        resp = self.fetch("/api/v1/jobs/done1")
        assert resp.code == 200
        body = json.loads(resp.body)
        assert body["status"] == "done"
        assert body["result"] == {"built": ["a"]}

    def test_running_job_status(self):
        resp = self.fetch("/api/v1/jobs/run1")
        assert resp.code == 200
        body = json.loads(resp.body)
        assert body["status"] == "running"
        assert body["stage"] == "meshing"
        assert "result" not in body

    def test_unknown_job_404(self):
        resp = self.fetch("/api/v1/jobs/nope")
        assert resp.code == 404

    def test_cancel_running_job(self):
        resp = self.fetch("/api/v1/jobs/run1/cancel", method="POST", body=b"")
        assert resp.code == 200
        assert json.loads(resp.body)["cancelled"] is True

    def test_cancel_unknown_404(self):
        resp = self.fetch("/api/v1/jobs/nope/cancel", method="POST", body=b"")
        assert resp.code == 404
