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


@pytest.fixture
def service(tmp_path):
    # A model + its sidecars, an assembly scene, and a motion trajectory so every GET has content.
    (tmp_path / "box.gltf").write_text('{"asset": {"version": "2.0"}}')
    (tmp_path / "box.bom.json").write_text('{"floor_area": 24.0}')
    (tmp_path / "box.plan.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    (tmp_path / "box.elementmap.json").write_text('{"attribute_model_version": 2, "elements": []}')
    (tmp_path / "box.hierarchy.json").write_text('{"name": "box", "kind": "part", "children": []}')
    (tmp_path / "box.status.json").write_text('{"sketches": []}')
    (tmp_path / "widget.assembly.json").write_text('{"instances": [], "joints": []}')
    (tmp_path / "widget.motion.json").write_text('{"frames": [], "driver": {"joint": "j"}}')
    svc = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0,
                      build_service=_FakeBuildService())
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
    assert json.loads(body)["motions"] == ["widget"]
    status, body, _ = _get(f"{service.base_url}/api/v1/motion/widget")
    assert status == 200 and "frames" in json.loads(body)


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


def test_build_post(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/build", {"spec": "x.hocon"})
    assert status == 200
    payload = json.loads(body)
    assert payload["built"] == ["thing.glb"] and payload["build_ms"] == 1.0
    assert "models" in payload  # refreshed listing merged in


def test_assemble_post(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/assemble", {"spec": "x.asm.hocon"})
    payload = json.loads(body)
    assert payload["assembled"] == "asm" and payload["build_ms"] == 2.0
    assert "assemblies" in payload


def test_motion_build_post(service):
    status, body, _ = _post(f"{service.base_url}/api/v1/motion-build", {"spec": "x.motion.hocon"})
    payload = json.loads(body)
    assert payload["assembled"] == "asm" and payload["build_ms"] == 3.0
    assert "motions" in payload


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


def test_cors_header_on_get(service):
    # A future cross-origin (React) client relies on the permissive CORS header on every response.
    _status, _body, headers = _get(f"{service.base_url}/api/v1/models")
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_cors_preflight_options_returns_204(service):
    request = urllib.request.Request(f"{service.base_url}/api/v1/build", method="OPTIONS")
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 204
        assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
