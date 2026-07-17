"""Tests for the hand-authored OpenAPI spec + its drift guard against the live route table.

OpenApiSpec.document() returns an OpenAPI 3.1 dict. The drift guard asserts every /api/v1 route in
ApiRouter has a matching documented path (so a new route without docs fails the suite), and the
HTTP tests confirm /api/v1/openapi.json serves the spec and /docs serves Swagger UI HTML.
"""

import json
import re
import urllib.request

import pytest

from ncad.service.api_router import ApiRouter
from ncad.service.ncad_service import NcadService, make_deps
from ncad.service.openapi_spec import OpenApiSpec


def _documented_paths() -> set[str]:
    return set(OpenApiSpec().document()["paths"].keys())


def _live_api_paths() -> set[str]:
    # The /api/v1 routes from the live table, with Tornado's (.+) capture turned into an OpenAPI
    # {name} template so they compare against the documented path keys.
    deps = make_deps(models_dir="/tmp", examples_dir=None, dev=True, boot_id="x")
    paths: set[str] = set()
    for rule in ApiRouter().rules(deps):
        pattern = rule.matcher.regex.pattern.rstrip("$")
        if not pattern.startswith("/api/v1"):
            continue
        paths.add(re.sub(r"\(\.\+\)", "{name}", pattern))
    return paths


def test_document_is_openapi_3():
    doc = OpenApiSpec().document()
    assert doc["openapi"].startswith("3.")
    assert doc["info"]["title"] == "ncad API"
    assert isinstance(doc["paths"], dict) and doc["paths"]


def test_every_live_api_route_is_documented():
    # Drift guard: no /api/v1 route may exist without an OpenAPI entry.
    missing = _live_api_paths() - _documented_paths()
    assert not missing, f"undocumented /api/v1 routes: {sorted(missing)}"


def test_no_documented_path_is_dead():
    # And no documented path should reference a route that no longer exists.
    stale = _documented_paths() - _live_api_paths()
    assert not stale, f"documented paths with no live route: {sorted(stale)}"


@pytest.fixture
def service(tmp_path):
    svc = NcadService(models_dir=str(tmp_path), host="127.0.0.1", port=0, dev=False)
    svc.start()
    try:
        yield svc
    finally:
        svc.stop()


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read(), response.headers


def test_openapi_json_route(service):
    status, body, headers = _get(f"{service.base_url}/api/v1/openapi.json")
    assert status == 200
    assert "application/json" in headers["Content-Type"]
    doc = json.loads(body)
    assert doc["openapi"].startswith("3.")


def test_docs_route_serves_swagger_html(service):
    status, body, headers = _get(f"{service.base_url}/docs")
    assert status == 200
    assert "text/html" in headers["Content-Type"]
    text = body.decode("utf-8")
    assert "swagger" in text.lower()
    assert "/api/v1/openapi.json" in text
