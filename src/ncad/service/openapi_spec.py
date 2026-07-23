"""Hand-authored OpenAPI 3.1 document for the ncad JSON API (served at /api/v1/openapi.json).

One class, ``document() -> dict``. Every /api/v1 route has a ``paths`` entry with its method, path
params, request body (the ``{"spec": ...}`` POST bodies), and response schemas (the 200 shape plus
the shared ``{"error": ...}`` envelope). A drift-guard test asserts this stays in lockstep with the
live route table, so a new route without docs fails the suite. Kept hand-authored (no schema-gen
dependency): full control, zero new deps, trivially testable - matching the neuro-san approach of
publishing a static OpenAPI document.
"""

from typing import Any

_VERSION = "1.0.0"

# Reusable response fragments.
_ERROR = {"description": "error", "content": {"application/json": {
    "schema": {"type": "object", "properties": {"error": {"type": "string"}}}}}}
_JSON_OK = {"description": "ok", "content": {"application/json": {
    "schema": {"type": "object"}}}}
_NAME_PARAM = [{"name": "name", "in": "path", "required": True,
                "schema": {"type": "string"},
                "description": "the resource name (URL-encoded)"}]
_SPEC_BODY = {"required": True, "content": {"application/json": {"schema": {
    "type": "object", "required": ["spec"],
    "properties": {"spec": {"type": "string",
                            "description": "example spec path or a recorded source"}}}}}}


def _get_collection(summary: str) -> dict:
    """A GET returning a JSON collection object."""
    return {"get": {"summary": summary, "responses": {"200": _JSON_OK}}}


def _get_by_name(summary: str, not_found: str) -> dict:
    """A GET of a named resource (200 or 404)."""
    return {"get": {"summary": summary, "parameters": _NAME_PARAM,
                    "responses": {"200": _JSON_OK, "404": _ERROR}}}


def _get_bytes(summary: str, media: str, not_found: str) -> dict:
    """A GET returning bytes/SVG of a named resource (200 or 404)."""
    return {"get": {"summary": summary, "parameters": _NAME_PARAM,
                    "responses": {"200": {"description": "ok",
                                          "content": {media: {}}},
                                  "404": _ERROR}}}


def _post_build(summary: str) -> dict:
    """A POST taking a {"spec": ...} body (200, 400 on bad request / rejected)."""
    return {"post": {"summary": summary, "requestBody": _SPEC_BODY,
                     "responses": {"200": _JSON_OK, "400": _ERROR, "500": _ERROR}}}


def _post_delete(summary: str) -> dict:
    """A POST that deletes a named resource (200 or 404)."""
    return {"post": {"summary": summary, "parameters": _NAME_PARAM,
                     "responses": {"200": _JSON_OK, "404": _ERROR}}}


class OpenApiSpec:
    """Builds the ncad API OpenAPI 3.1 document."""

    def document(self) -> dict[str, Any]:
        """Return the OpenAPI 3.1 spec dict for every /api/v1 route."""
        paths: dict[str, Any] = {
            "/api/v1/specs": _get_collection("List example spec documents (tree)."),
            "/api/v1/models": _get_collection("List built models with their recorded sources."),
            "/api/v1/assemblies": _get_collection("List composed assembly scenes."),
            "/api/v1/motions": _get_collection("List assemblies that have a motion trajectory."),
            "/api/v1/motion/{name}": _get_by_name(
                "Get an assembly's motion trajectory.", "no motion for assembly"),
            "/api/v1/robots": _get_collection("List robots (assemblies with a .robot.json)."),
            "/api/v1/robot/{name}": _get_by_name(
                "Get a robot's tree (links + joints + computed inertia).", "unknown robot"),
            "/api/v1/robot-sweeps/{name}": _get_by_name(
                "Get a robot's per-joint articulation sweeps.", "no sweeps for robot"),
            "/api/v1/bom/{name}": _get_by_name("Get a model's BOM.", "no BOM for model"),
            "/api/v1/plan/{name}": _get_bytes(
                "Get a model's plan SVG.", "image/svg+xml", "no plan for model"),
            "/api/v1/elementmap/{name}": _get_by_name(
                "Get a model's element map.", "no element map for model"),
            "/api/v1/hierarchy/{name}": _get_by_name(
                "Get a model's feature hierarchy.", "no hierarchy for model"),
            "/api/v1/status/{name}": _get_by_name(
                "Get a model's sketch status.", "no sketch status for model"),
            "/api/v1/build": _post_build(
                "Build a part spec. Returns {models, built, build_ms}."),
            "/api/v1/assemble": _post_build(
                "Compose an assembly. Returns {assemblies, assembled, issues, build_ms}."),
            "/api/v1/motion-build": _post_build(
                "Run a motion study. Returns {motions, assembled, issues, build_ms}."),
            "/api/v1/physics-build": _post_build(
                "Export a robot + sidecars. Returns {robots, robot, warnings, build_ms}."),
            "/api/v1/robot-collide": _post_build(
                "Check a robot's self-collision at a pose. Returns {collisions}."),
            "/api/v1/export": _post_build(
                "Re-export a model to a format; streams the file as a download."),
            "/api/v1/validate": _post_build(
                "Validate a spec without building. Returns {ok, diagnostics}."),
            "/api/v1/models/{name}/delete": _post_delete("Delete a model and its sidecars."),
            "/api/v1/assembly/{name}/delete": _post_delete(
                "Delete an assembly scene and its motion sidecar."),
            "/api/v1/robot/{name}/delete": _post_delete(
                "Delete a robot's tree + sweeps sidecars."),
            "/api/v1/assembly/{name}": _get_by_name(
                "Get an assembly scene.", "unknown assembly"),
            "/api/v1/models/{name}": _get_bytes(
                "Get model bytes (glb/gltf/bin/png).", "application/octet-stream", "unknown model"),
            "/api/v1/openapi.json": _get_collection("This OpenAPI document."),
        }
        return {
            "openapi": "3.1.0",
            "info": {"title": "ncad API", "version": _VERSION,
                     "description": "Build, compose, and drive parametric CAD documents; "
                                    "list and fetch the resulting models and sidecars."},
            "paths": paths,
        }
