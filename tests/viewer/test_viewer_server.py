"""Integration tests for the viewer HTTP server.

Starts the server on an ephemeral port in a background thread and exercises its routes.
No browser needed; these check the HTTP contract the frontend depends on.
"""

import json
import urllib.request

import pytest

from ncad.viewer.viewer_server import ViewerServer


@pytest.fixture
def server(tmp_path):
    (tmp_path / "box.gltf").write_text('{"asset": {"version": "2.0"}}')
    (tmp_path / "box.bom.json").write_text('{"floor_area": 24.0, "door_count": 1}')
    (tmp_path / "box.plan.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
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
    assert json.loads(body) == {"models": ["box.gltf"]}


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
