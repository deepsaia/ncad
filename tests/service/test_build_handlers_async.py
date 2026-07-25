import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from ncad.service.api_router import ApiRouter
from ncad.service.build_job import BuildJob
from ncad.service.job_manager import SaturatedError


class FakeManager:
    """Stands in for JobManager: records submits, returns a queued job or raises SaturatedError."""

    def __init__(self):
        self.calls = []
        self.saturated = False

    def submit(self, kind, payload, coalesce_key):
        if self.saturated:
            raise SaturatedError("busy")
        self.calls.append((kind, payload, coalesce_key))
        return BuildJob(id="job42", kind=kind, spec=coalesce_key or "", status="running",
                        stage="queued", stages_done=0, stages_total=0, message="", result=None,
                        error=None, created_at=0.0, finished_at=None)

    def get(self, job_id):
        return None

    def cancel(self, job_id):
        return False


def _app(mgr):
    deps = {"catalog": None, "spec_catalog": None, "build_service": None, "page": None,
            "dev": False, "boot_id": "b", "job_manager": mgr, "config": None}
    return Application(ApiRouter().rules(deps))


class BuildAsyncTest(AsyncHTTPTestCase):
    def get_app(self):
        self.mgr = FakeManager()
        return _app(self.mgr)

    def test_build_returns_202_and_job_id(self):
        resp = self.fetch("/api/v1/build", method="POST",
                          body=json.dumps({"spec": "a.hocon"}).encode())
        assert resp.code == 202
        assert json.loads(resp.body)["job_id"] == "job42"
        assert self.mgr.calls == [("build", {"spec": "a.hocon"}, "a.hocon")]

    def test_analyze_maps_to_analyze_kind(self):
        self.fetch("/api/v1/analyze", method="POST",
                   body=json.dumps({"spec": "c.analysis.hocon"}).encode())
        assert self.mgr.calls[0][0] == "analyze"

    def test_motion_maps_to_motion_kind(self):
        self.fetch("/api/v1/motion-build", method="POST",
                   body=json.dumps({"spec": "m.motion.hocon"}).encode())
        assert self.mgr.calls[0][0] == "motion"

    def test_physics_maps_to_physics_kind(self):
        self.fetch("/api/v1/physics-build", method="POST",
                   body=json.dumps({"spec": "p.physics.hocon"}).encode())
        assert self.mgr.calls[0][0] == "physics"

    def test_bad_body_is_400(self):
        resp = self.fetch("/api/v1/build", method="POST", body=b"{}")
        assert resp.code == 400

    def test_saturation_is_503(self):
        self.mgr.saturated = True
        resp = self.fetch("/api/v1/assemble", method="POST",
                          body=json.dumps({"spec": "a.hocon"}).encode())
        assert resp.code == 503
