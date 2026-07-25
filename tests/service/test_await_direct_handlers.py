import base64
import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from ncad.service.api_router import ApiRouter


class FakeManager:
    """arun_direct returns a preset worker-result dict; records the calls."""

    def __init__(self):
        self.calls = []
        self.results = {}

    async def arun_direct(self, kind, payload):
        self.calls.append((kind, payload))
        return self.results[kind]

    def get(self, job_id):
        return None


def _app(mgr):
    deps = {"catalog": None, "spec_catalog": None, "build_service": None, "page": None,
            "dev": False, "boot_id": "b", "job_manager": mgr, "config": None}
    return Application(ApiRouter().rules(deps))


class AwaitDirectTest(AsyncHTTPTestCase):
    def get_app(self):
        self.mgr = FakeManager()
        return _app(self.mgr)

    def test_export_streams_decoded_bytes(self):
        self.mgr.results["export"] = {"ok": True, "result": {
            "download_name": "part.step", "content_type": "model/step",
            "data_b64": base64.b64encode(b"SOLID").decode("ascii")}}
        resp = self.fetch("/api/v1/export", method="POST", body=json.dumps(
            {"name": "part.glb", "kind": "part", "format": "step"}).encode())
        assert resp.code == 200
        assert resp.body == b"SOLID"
        assert resp.headers["Content-Disposition"] == 'attachment; filename="part.step"'
        assert self.mgr.calls[0][0] == "export"

    def test_export_failure_is_400(self):
        self.mgr.results["export"] = {"ok": False, "error": "unknown model"}
        resp = self.fetch("/api/v1/export", method="POST", body=json.dumps(
            {"name": "x", "kind": "part", "format": "step"}).encode())
        assert resp.code == 400

    def test_robot_collide_returns_result_json(self):
        self.mgr.results["robot-collide"] = {"ok": True, "result": {"collisions": []}}
        resp = self.fetch("/api/v1/robot-collide", method="POST", body=json.dumps(
            {"name": "arm", "pose": {"j1": 0.5}}).encode())
        assert resp.code == 200
        assert json.loads(resp.body) == {"collisions": []}

    def test_validate_returns_report(self):
        self.mgr.results["validate"] = {"ok": True, "result": {"ok": True, "diagnostics": []}}
        resp = self.fetch("/api/v1/validate", method="POST",
                          body=json.dumps({"spec": "a.hocon"}).encode())
        assert resp.code == 200
        assert json.loads(resp.body)["ok"] is True
