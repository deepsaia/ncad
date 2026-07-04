"""Integration tests for the viewer HTTP server.

Starts the server on an ephemeral port in a background thread and exercises its routes.
No browser needed; these check the HTTP contract the frontend depends on.
"""

import json
import urllib.error
import urllib.request

import pytest

from ncad.viewer.viewer_server import ViewerServer


@pytest.fixture
def server(tmp_path):
    (tmp_path / "box.gltf").write_text('{"asset": {"version": "2.0"}}')
    (tmp_path / "box.bom.json").write_text('{"floor_area": 24.0, "door_count": 1}')
    (tmp_path / "box.plan.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    (tmp_path / "box.elementmap.json").write_text(
        '{"attribute_model_version": 1, "elements": ['
        '{"index": 0, "id": "pad/cap(+Z)/0", "kind": "face", '
        '"created_by": "pad", "tag": "cap(+Z)"}]}')
    (tmp_path / "box.hierarchy.json").write_text(
        '{"name": "box", "kind": "part", "op": "solid", "children": ['
        '{"id": "pad", "kind": "feature", "op": "extrude", "children": []}]}')
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read(), response.headers


def test_index_serves_html(server) -> None:
    status, body, headers = _get(f"{server.base_url}/")

    assert status == 200
    assert b"<!DOCTYPE html>" in body or b"<!doctype html>" in body
    assert "text/html" in headers["Content-Type"]


def test_deep_link_to_model_serves_spa(server) -> None:
    # /<model>.glb (a known model) serves the SPA HTML so the viewer can preselect it.
    status, body, headers = _get(f"{server.base_url}/box.gltf")

    assert status == 200
    assert "text/html" in headers["Content-Type"]
    assert b"</html>" in body


def test_deep_link_to_unknown_model_404s(server) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(f"{server.base_url}/nope.glb")

    assert exc.value.code == 404


def test_query_string_is_ignored_for_routing(server) -> None:
    # A trailing query string must not break route matching (regression).
    status, body, _ = _get(f"{server.base_url}/?foo=bar")

    assert status == 200
    assert b"</html>" in body


def test_api_models_lists_models(server) -> None:
    status, body, headers = _get(f"{server.base_url}/api/models")

    assert status == 200
    assert "application/json" in headers["Content-Type"]
    assert json.loads(body) == {"models": [{"name": "box.gltf", "source": None}]}


def test_model_bytes_are_served(server) -> None:
    status, body, headers = _get(f"{server.base_url}/models/box.gltf")

    assert status == 200
    assert b'"version": "2.0"' in body


def test_unknown_model_returns_404(server) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(f"{server.base_url}/models/nope.gltf")

    assert exc.value.code == 404


def test_path_traversal_is_rejected(server) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(f"{server.base_url}/models/..%2fsecret.gltf")

    assert exc.value.code in (400, 404)


def test_bom_endpoint_returns_sidecar_json(server) -> None:
    status, body, headers = _get(f"{server.base_url}/api/bom/box.gltf")

    assert status == 200
    assert "application/json" in headers["Content-Type"]
    assert json.loads(body) == {"floor_area": 24.0, "door_count": 1}


def test_bom_endpoint_404_when_no_sidecar(tmp_path) -> None:
    (tmp_path / "lonely.glb").write_bytes(b"glTF\x02\x00\x00\x00")  # model, no .bom.json
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(f"{srv.base_url}/api/bom/lonely.glb")
        assert exc.value.code == 404
    finally:
        srv.stop()


def test_elementmap_endpoint_returns_sidecar_json(server) -> None:
    status, body, headers = _get(f"{server.base_url}/api/elementmap/box.gltf")

    assert status == 200
    assert "application/json" in headers["Content-Type"]
    data = json.loads(body)
    assert data["attribute_model_version"] == 1
    assert data["elements"][0]["id"] == "pad/cap(+Z)/0"


def test_elementmap_endpoint_404_when_no_sidecar(tmp_path) -> None:
    (tmp_path / "lonely.glb").write_bytes(b"glTF\x02\x00\x00\x00")
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(f"{srv.base_url}/api/elementmap/lonely.glb")
        assert exc.value.code == 404
    finally:
        srv.stop()


def test_hierarchy_endpoint_returns_sidecar_json(server) -> None:
    status, body, headers = _get(f"{server.base_url}/api/hierarchy/box.gltf")

    assert status == 200
    assert "application/json" in headers["Content-Type"]
    data = json.loads(body)
    assert data["name"] == "box"
    assert data["children"][0]["id"] == "pad"


def test_hierarchy_endpoint_404_when_no_sidecar(tmp_path) -> None:
    (tmp_path / "lonely.glb").write_bytes(b"glTF\x02\x00\x00\x00")
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(f"{srv.base_url}/api/hierarchy/lonely.glb")
        assert exc.value.code == 404
    finally:
        srv.stop()


def test_plan_endpoint_returns_svg(server) -> None:
    status, body, headers = _get(f"{server.base_url}/api/plan/box.gltf")

    assert status == 200
    assert "image/svg+xml" in headers["Content-Type"]
    assert b"</svg>" in body


def test_plan_endpoint_404_when_no_sidecar(tmp_path) -> None:
    (tmp_path / "lonely.glb").write_bytes(b"glTF\x02\x00\x00\x00")
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(f"{srv.base_url}/api/plan/lonely.glb")
        assert exc.value.code == 404
    finally:
        srv.stop()


def test_gltf_companion_bin_buffer_is_served(tmp_path) -> None:
    """Regression: a text .gltf references an external .bin buffer the loader fetches.

    The server must serve that sidecar, or models fail to load in the browser.
    """
    (tmp_path / "m.gltf").write_text('{"buffers":[{"uri":"m.bin"}]}')
    (tmp_path / "m.bin").write_bytes(b"\x01\x02\x03\x04")
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        status, body, headers = _get(f"{srv.base_url}/models/m.bin")
        assert status == 200
        assert body == b"\x01\x02\x03\x04"
        assert "octet-stream" in headers["Content-Type"]
    finally:
        srv.stop()


def test_glb_served_with_binary_content_type(tmp_path) -> None:
    (tmp_path / "m.glb").write_bytes(b"glTF\x02\x00\x00\x00")
    srv = ViewerServer(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    srv.start()
    try:
        status, body, headers = _get(f"{srv.base_url}/models/m.glb")
        assert status == 200
        assert "model/gltf-binary" in headers["Content-Type"]
    finally:
        srv.stop()


# ---- New routes: /api/specs, /api/build, delete (Task 5) ----

from ncad.viewer.build_service import BuildError  # noqa: E402


class _StubBuildService:
    """Stub build service so route tests stay fast (no OCP)."""

    def __init__(self) -> None:
        self.calls = []

    def build(self, spec: str) -> dict:
        self.calls.append(spec)
        if spec == "bad.hocon":
            raise BuildError("nope")
        return {"built": ["block.glb"]}


def test_api_specs_returns_tree(tmp_path) -> None:
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    models = tmp_path / "out"
    models.mkdir()
    srv = ViewerServer(str(models), port=0, examples_dir=str(examples))
    srv.start()
    try:
        status, body, _ = _get(f"{srv.base_url}/api/specs")
    finally:
        srv.stop()

    assert status == 200
    assert json.loads(body)["tree"][0]["name"] == "g"


def test_api_models_carries_source(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    (models / "block.glb").write_bytes(b"x")
    (models / "block.meta.json").write_text('{"source": "g/block.hocon"}')
    srv = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    srv.start()
    try:
        status, body, _ = _get(f"{srv.base_url}/api/models")
    finally:
        srv.stop()

    assert json.loads(body)["models"] == [{"name": "block.glb", "source": "g/block.hocon"}]


def _post(url: str, payload: dict | None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, response.read()


def test_api_build_success(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    stub = _StubBuildService()
    srv = ViewerServer(str(models), port=0, examples_dir=str(tmp_path), build_service=stub)
    srv.start()
    try:
        status, body = _post(f"{srv.base_url}/api/build", {"spec": "g/block.hocon"})
    finally:
        srv.stop()

    assert status == 200
    data = json.loads(body)
    assert stub.calls == ["g/block.hocon"]
    assert data["built"] == ["block.glb"]
    assert "models" in data


def test_api_build_error_returns_400(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    srv = ViewerServer(
        str(models), port=0, examples_dir=str(tmp_path), build_service=_StubBuildService()
    )
    srv.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            _post(f"{srv.base_url}/api/build", {"spec": "bad.hocon"})
        assert exc.value.code == 400
        assert "error" in json.loads(exc.value.read())
    finally:
        srv.stop()


def test_api_delete_removes_and_returns_list(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    (models / "block.glb").write_bytes(b"x")
    srv = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    srv.start()
    try:
        status, body = _post(f"{srv.base_url}/api/models/block.glb/delete", None)
    finally:
        srv.stop()

    assert status == 200
    assert json.loads(body)["models"] == []
    assert not (models / "block.glb").exists()


def test_index_contains_new_ui_elements(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    srv = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    srv.start()
    try:
        _, body, _ = _get(f"{srv.base_url}/")
        html = body.decode()
    finally:
        srv.stop()

    for token in (
        'id="spec-search"', 'id="spec-tree"', 'id="spec-build"', 'id="model-list"',
        'id="viewport-controls"', 'id="theme-toggle"', 'data-theme="light"]',
    ):
        assert token in html


@pytest.mark.slow
def test_real_build_route_produces_model(tmp_path) -> None:
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    examples = repo / "examples"
    models = tmp_path / "out"
    models.mkdir()
    srv = ViewerServer(str(models), port=0, examples_dir=str(examples))
    srv.start()
    try:
        status, body = _post(
            f"{srv.base_url}/api/build", {"spec": "gate-0.1-first-shape/block.hocon"}
        )
    finally:
        srv.stop()

    assert status == 200
    data = json.loads(body)
    assert "block.glb" in data["built"]
    assert (models / "block.glb").is_file()
    assert (models / "block.meta.json").is_file()
