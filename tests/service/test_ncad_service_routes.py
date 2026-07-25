"""HTTP-contract tests for every /api/v1 route on the Tornado service.

Starts NcadService on an ephemeral port and exercises the routes with urllib, asserting status +
JSON/bytes/content-type + the error contract. A fake BuildService is injected so build/assemble/
motion-build are exercised without the geometry kernel. The delete-not-405 test guards the route
ordering (Tornado matches by URL only, so the delete POSTs must precede the GET catch-alls).
"""

import json
import urllib.error
import urllib.request

import pytest

from ncad.service.ncad_service import NcadService


class _FakeBuildService:
    """A BuildService stand-in: records calls, returns canned results, no kernel."""

    def build(self, spec: str) -> dict:
        return {"built": ["thing.glb"], "build_ms": 1.0}

    def assemble(self, spec: str) -> dict:
        return {"assembled": "asm", "issues": [], "build_ms": 2.0}

    def build_motion(self, spec: str) -> dict:
        return {"assembled": "asm", "issues": [], "build_ms": 3.0}

    def build_physics(self, spec: str) -> dict:
        return {"robot": "arm", "warnings": [], "build_ms": 4.0}

    def analyze(self, spec: str) -> dict:
        return {"analysis": "bracket", "status": "generated", "summary": {"max_von_mises": 1.0},
                "warnings": [], "build_ms": 5.0}

    def check_robot_collision(self, name: str, pose: dict) -> dict:
        return {"collisions": [{"a": "forearm", "b": "base", "volume": 123.4}]}

    def read_robot_keyframes(self, name: str) -> dict:
        return {"sets": {"wave": [{"time": 0, "pose": {}}, {"time": 1, "pose": {}}]}}

    def save_robot_keyframes(self, name: str, set_name: str, keyframes: list) -> dict:
        return {"sets": [set_name]}

    def export_model(self, name: str, kind: str, fmt: str) -> tuple[str, str, bytes]:
        return (f"{name}.{fmt}", "application/step", b"ISO-10303-21;\n")

    def validate(self, spec: str) -> dict:
        return {"ok": True, "diagnostics": []}


class _FakeJobManager:
    """Runs the fake build service synchronously and stores a done job, so a poll returns it.

    The real JobManager offloads to a spawn worker (which builds its own BuildService), bypassing
    the injected fake; this stand-in keeps the route contract testable without a subprocess.
    """

    _DISPATCH = {
        "build": lambda s, p: s.build(p["spec"]),
        "assemble": lambda s, p: s.assemble(p["spec"]),
        "motion": lambda s, p: s.build_motion(p["spec"]),
        "physics": lambda s, p: s.build_physics(p["spec"]),
        "analyze": lambda s, p: s.analyze(p["spec"]),
    }

    def __init__(self, build_service):
        self._svc = build_service
        self._jobs: dict = {}
        self._n = 0

    def submit(self, kind, payload, coalesce_key):
        from ncad.service.build_job import BuildJob

        self._n += 1
        job_id = f"job{self._n}"
        result = self._DISPATCH[kind](self._svc, payload)
        job = BuildJob(id=job_id, kind=kind, spec=coalesce_key or "", status="done",
                       stage="done", stages_done=1, stages_total=1, message="", result=result,
                       error=None, created_at=0.0, finished_at=1.0)
        self._jobs[job_id] = job
        return job

    def get(self, job_id):
        return self._jobs.get(job_id)

    def cancel(self, job_id):
        return False

    def shutdown(self, timeout_s):
        pass

    async def arun_direct(self, kind, payload):
        import base64

        if kind == "validate":
            return {"ok": True, "result": self._svc.validate(payload["spec"])}
        if kind == "robot-collide":
            return {"ok": True,
                    "result": self._svc.check_robot_collision(payload["name"], payload["pose"])}
        if kind == "export":
            name, content_type, data = self._svc.export_model(
                payload["name"], payload["kind"], payload["format"])
            return {"ok": True, "result": {
                "download_name": name, "content_type": content_type,
                "data_b64": base64.b64encode(data).decode("ascii")}}
        raise AssertionError(f"unexpected arun_direct kind {kind!r}")


@pytest.fixture
def service(tmp_path):
    # A model + its sidecars, an assembly scene, and a motion trajectory so every GET has content,
    # laid out in the out/<kind>/<name>/ tree the catalog now reads.
    part = tmp_path / "parts" / "box"
    part.mkdir(parents=True)
    (part / "box.gltf").write_text('{"asset": {"version": "2.0"}}')
    (part / "box.bom.json").write_text('{"floor_area": 24.0}')
    (part / "box.plan.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    (part / "box.elementmap.json").write_text('{"attribute_model_version": 2, "elements": []}')
    (part / "box.hierarchy.json").write_text('{"name": "box", "kind": "part", "children": []}')
    (part / "box.status.json").write_text('{"sketches": []}')
    asm = tmp_path / "assemblies" / "widget"
    asm.mkdir(parents=True)
    (asm / "widget.assembly.json").write_text('{"instances": [], "joints": []}')
    (asm / "widget.motion.json").write_text('{"frames": [], "driver": {"joint": "j"}}')
    robot = tmp_path / "robots" / "arm"
    robot.mkdir(parents=True)
    (robot / "arm.robot.json").write_text(
        '{"base_link": "b", "links": [{"name": "b"}], "joints": [{"name": "j1"}]}')
    (robot / "arm.robot_sweeps.json").write_text('{"j1": {"from": 0, "to": 1, "frames": []}}')
    analysis = tmp_path / "analyses" / "bracket"
    analysis.mkdir(parents=True)
    (analysis / "bracket.analysis.json").write_text('{"summary": {"max_von_mises": 423646.0}}')
    (analysis / "bracket.analysis.mesh.json").write_text(
        '{"points": [[0,0,0]], "triangles": [], "fields": {}, "ranges": {}}')
    fake_build = _FakeBuildService()
    svc = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0,
                      build_service=fake_build, job_manager=_FakeJobManager(fake_build))
    svc.start()
    try:
        yield svc
    finally:
        svc.stop()


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read(), response.headers


def _post(url: str, payload: dict | None):
    data = json.dumps(payload).encode() if payload is not None else b""
    request = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, response.read(), response.headers


def test_models_list(service):
    status, body, headers = _get(f"{service.base_url}/api/v1/models")
    assert status == 200
    payload = json.loads(body)
    assert [m["name"] for m in payload["models"]] == ["box.gltf"]


def test_model_bytes(service):
    status, body, headers = _get(f"{service.base_url}/api/v1/models/box.gltf")
    assert status == 200
    assert headers["Content-Type"] == "model/gltf+json"
    assert b'"asset"' in body


def test_model_bytes_unknown_404(service):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(f"{service.base_url}/api/v1/models/nope.glb")
    assert exc.value.code == 404


def test_assemblies_list_and_scene(service):
    status, body, _ = _get(f"{service.base_url}/api/v1/assemblies")
    assert json.loads(body)["assemblies"] == ["widget"]
    status, body, headers = _get(f"{service.base_url}/api/v1/assembly/widget")
    assert status == 200 and "application/json" in headers["Content-Type"]
    assert "instances" in json.loads(body)


def test_motions_list_and_trajectory(service):
    status, body, _ = _get(f"{service.base_url}/api/v1/motions")
    # Labeled shape: [{name, label}]; this fixture's driver declares neither fps nor steps and has
    # no frames, so the label is None (the row still lists).
    assert json.loads(body)["motions"] == [{"name": "widget", "label": None}]
    status, body, _ = _get(f"{service.base_url}/api/v1/motion/widget")
    assert status == 200 and "frames" in json.loads(body)


def test_robots_list_tree_and_sweeps(service):
    status, body, _ = _get(f"{service.base_url}/api/v1/robots")
    assert status == 200
    assert json.loads(body)["robots"] == [{"name": "arm", "label": "1j", "source": None}]
    status, body, _ = _get(f"{service.base_url}/api/v1/robot/arm")
    assert status == 200 and "links" in json.loads(body)
    status, body, _ = _get(f"{service.base_url}/api/v1/robot-sweeps/arm")
    assert status == 200 and "j1" in json.loads(body)


@pytest.mark.parametrize("route,ctype", [
    ("bom/box.gltf", "application/json"),
    ("plan/box.gltf", "image/svg+xml; charset=utf-8"),
    ("elementmap/box.gltf", "application/json"),
    ("hierarchy/box.gltf", "application/json"),
    ("status/box.gltf", "application/json"),
])
def test_sidecar_routes(service, route, ctype):
    status, body, headers = _get(f"{service.base_url}/api/v1/{route}")
    assert status == 200
    assert headers["Content-Type"] == ctype


def _submit_and_poll(service, endpoint: str, spec: str) -> dict:
    """POST a build (expect 202 + job_id), then GET the job once; return its result dict."""
    status, body, _ = _post(f"{service.base_url}/api/v1/{endpoint}", {"spec": spec})
    assert status == 202
    job_id = json.loads(body)["job_id"]
    status, body, _ = _get(f"{service.base_url}/api/v1/jobs/{job_id}")
    assert status == 200
    job = json.loads(body)
    assert job["status"] == "done"
    return job["result"]


def test_build_post(service):
    result = _submit_and_poll(service, "build", "x.hocon")
    assert result["built"] == ["thing.glb"] and result["build_ms"] == 1.0


def test_assemble_post(service):
    result = _submit_and_poll(service, "assemble", "x.asm.hocon")
    assert result["assembled"] == "asm" and result["build_ms"] == 2.0


def test_motion_build_post(service):
    result = _submit_and_poll(service, "motion-build", "x.motion.hocon")
    assert result["assembled"] == "asm" and result["build_ms"] == 3.0


def test_physics_build_post(service):
    result = _submit_and_poll(service, "physics-build", "x.physics.hocon")
    assert result["robot"] == "arm" and result["build_ms"] == 4.0


def test_robot_collide_post(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/robot-collide",
                            {"name": "arm", "pose": {"elbow": 3.14}})
    assert status == 200
    collisions = json.loads(body)["collisions"]
    assert collisions and collisions[0]["a"] == "forearm" and collisions[0]["b"] == "base"


def test_analyses_list_summary_and_mesh(service):
    status, body, _ = _get(f"{service.base_url}/api/v1/analyses")
    assert status == 200
    assert [a["name"] for a in json.loads(body)["analyses"]] == ["bracket"]
    status, body, _ = _get(f"{service.base_url}/api/v1/analysis/bracket")
    assert status == 200 and "summary" in json.loads(body)
    status, body, _ = _get(f"{service.base_url}/api/v1/analysis-mesh/bracket")
    assert status == 200 and "points" in json.loads(body)


def test_analyze_post(service):
    result = _submit_and_poll(service, "analyze", "bracket.analysis.hocon")
    assert result["analysis"] == "bracket" and result["status"] == "generated"


def test_robot_keyframes_get(service):
    status, body, _ = _get(f"{service.base_url}/api/v1/robot-keyframes/arm")
    assert status == 200
    assert "wave" in json.loads(body)["sets"]


def test_robot_keyframes_post_saves_a_named_set(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/robot-keyframes/arm",
                            {"set": "wave", "keyframes": [{"time": 0, "pose": {}}]})
    assert status == 200
    assert json.loads(body)["sets"] == ["wave"]


def test_export_post_streams_a_download(service):
    status, body, headers = _post(f"{service.base_url}/api/v1/export",
                                  {"name": "widget", "kind": "part", "format": "step"})
    assert status == 200
    assert headers["Content-Type"] == "application/step"
    assert 'attachment; filename="widget.step"' in headers["Content-Disposition"]
    assert body == b"ISO-10303-21;\n"


def test_validate_post(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/validate", {"spec": "box.hocon"})
    assert status == 200
    payload = json.loads(body)
    assert "ok" in payload and "diagnostics" in payload


def test_validate_post_missing_spec_400(service):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(f"{service.base_url}/api/v1/validate", {"not_spec": 1})
    assert exc.value.code == 400


def test_build_post_missing_spec_400(service):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _post(f"{service.base_url}/api/v1/build", {"not_spec": 1})
    assert exc.value.code == 400
    assert json.loads(exc.value.read())["error"]


def test_model_delete_returns_200_not_405(service):
    # Guards the route ordering: the delete POST must NOT be shadowed by the GET bytes catch-all.
    status, body, _ = _post(f"{service.base_url}/api/v1/models/box.gltf/delete", None)
    assert status == 200
    assert "models" in json.loads(body)


def test_assembly_delete_returns_200_not_405(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/assembly/widget/delete", None)
    assert status == 200
    assert json.loads(body)["assemblies"] == []


def test_robot_delete_returns_200_not_405(service):
    # Guards route ordering: POST /robot/<name>/delete must precede the GET /robot/(.+) catch-all.
    status, body, _ = _post(f"{service.base_url}/api/v1/robot/arm/delete", None)
    assert status == 200
    assert json.loads(body)["robots"] == []   # the only robot was just deleted


def test_analysis_delete_returns_200_not_405(service):
    # Guards route ordering: POST /analysis/<name>/delete must precede the GET /analysis/(.+)
    # catch-all AND the /analysis-mesh/ prefix must not shadow it.
    status, body, _ = _post(f"{service.base_url}/api/v1/analysis/bracket/delete", None)
    assert status == 200
    assert json.loads(body)["analyses"] == []   # the only analysis was just deleted


def test_cors_header_on_get(service):
    # A future cross-origin (React) client relies on the permissive CORS header on every response.
    _status, _body, headers = _get(f"{service.base_url}/api/v1/models")
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_cors_preflight_options_returns_204(service):
    request = urllib.request.Request(f"{service.base_url}/api/v1/build", method="OPTIONS")
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 204
        assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
