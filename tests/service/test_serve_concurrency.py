import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from ncad.service.api_router import ApiRouter


class _ModelsCatalog:
    def models_with_sources(self):
        return [{"name": "a.glb", "source": "a.hocon"}]


class NeverManager:
    """submit() 'accepts' a job but it never finishes; models GET must still return."""

    def submit(self, kind, payload, coalesce_key):
        from ncad.service.build_job import BuildJob
        return BuildJob(id="stuck", kind=kind, spec=coalesce_key or "", status="running",
                        stage="building", stages_done=0, stages_total=2, message="",
                        result=None, error=None, created_at=0.0, finished_at=None)

    def get(self, job_id):
        return None


def _app():
    deps = {"catalog": _ModelsCatalog(), "spec_catalog": None, "build_service": None,
            "page": None, "dev": False, "boot_id": "b",
            "job_manager": NeverManager(), "config": None}
    return Application(ApiRouter().rules(deps))


class ConcurrencyTest(AsyncHTTPTestCase):
    def get_app(self):
        return _app()

    def test_stuck_build_does_not_block_models_list(self):
        # Submit a build that never finishes.
        submit = self.fetch("/api/v1/build", method="POST",
                            body=json.dumps({"spec": "a.hocon"}).encode())
        assert submit.code == 202
        # A models GET must return immediately (the loop is not blocked by the build).
        models = self.fetch("/api/v1/models")
        assert models.code == 200
        assert json.loads(models.body)["models"][0]["name"] == "a.glb"
