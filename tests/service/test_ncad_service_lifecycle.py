"""Lifecycle tests for the Tornado NcadService: start on an ephemeral port, serve, stop.

Mirrors tests/viewer/test_viewer_server.py in spirit (real HTTP on an ephemeral port), but for
the Tornado service. Only the lifecycle + a couple of smoke routes here; per-route contract tests
live in test_ncad_service_routes.py.
"""

import urllib.error
import urllib.request

import pytest

from ncad.service.ncad_service import NcadService


@pytest.fixture
def service(tmp_path):
    (tmp_path / "box.gltf").write_text('{"asset": {"version": "2.0"}}')
    svc = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    svc.start()
    try:
        yield svc
    finally:
        svc.stop()


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read(), response.headers


def test_base_url_reports_bound_port(service):
    # port=0 picks an ephemeral free port; base_url must report the actual bound port.
    assert service.base_url.startswith("http://127.0.0.1:")
    assert service.base_url.rsplit(":", 1)[1] != "0"


def test_boot_id_is_stable_per_instance(service):
    # A single process/instance keeps one boot id (used by live-reload reconnect-and-compare).
    assert service.boot_id
    assert service.boot_id == service.boot_id


def test_two_instances_have_distinct_boot_ids(tmp_path):
    a = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    b = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0)
    assert a.boot_id != b.boot_id


def test_root_redirects_to_viewer(service):
    # GET / must 302 to /viewer (do not follow the redirect, just inspect it).
    request = urllib.request.Request(f"{service.base_url}/")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(request, timeout=5)
        raise AssertionError("expected a redirect, not a 200")
    except urllib.error.HTTPError as exc:
        assert exc.code == 302
        assert exc.headers["Location"] == "/viewer"


def test_specs_route_serves_json(service):
    status, body, headers = _get(f"{service.base_url}/api/v1/specs")
    assert status == 200
    assert "application/json" in headers["Content-Type"]
    assert b'"tree"' in body
