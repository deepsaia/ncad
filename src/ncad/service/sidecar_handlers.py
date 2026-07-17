"""Per-model sidecar routes: BOM, plan SVG, element map, hierarchy, sketch status.

Each handler resolves ``<model>.<sidecar>`` via the injected ModelCatalog and streams it with the
right content type, or 404s if absent. Small sibling classes over one resource family, grouped in
one module.
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


def _stream(handler: BaseApiHandler, resolved: str | None, content_type: str,
            missing: str) -> None:
    """Stream ``resolved`` with ``content_type``, or write a 404 ``missing`` error."""
    if resolved is None:
        handler.write_error_json(404, missing)
        return
    with open(resolved, "rb") as file_handle:
        handler.set_header("Content-Type", content_type)
        handler.safe_finish(file_handle.read())


class BomHandler(BaseApiHandler):
    """GET /api/v1/bom/<model> -> the BOM JSON sidecar."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the BOM sidecar, or 404."""
        _stream(self, self._catalog.resolve_bom(unquote(args[0])),
                "application/json", "no BOM for model")


class PlanHandler(BaseApiHandler):
    """GET /api/v1/plan/<model> -> the plan SVG sidecar."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the plan SVG, or 404."""
        _stream(self, self._catalog.resolve_plan(unquote(args[0])),
                "image/svg+xml; charset=utf-8", "no plan for model")


class ElementMapHandler(BaseApiHandler):
    """GET /api/v1/elementmap/<model> -> the element-map JSON sidecar."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the element-map sidecar, or 404."""
        _stream(self, self._catalog.resolve_elementmap(unquote(args[0])),
                "application/json", "no element map for model")


class HierarchyHandler(BaseApiHandler):
    """GET /api/v1/hierarchy/<model> -> the feature-hierarchy JSON sidecar."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the hierarchy sidecar, or 404."""
        _stream(self, self._catalog.resolve_hierarchy(unquote(args[0])),
                "application/json", "no hierarchy for model")


class StatusHandler(BaseApiHandler):
    """GET /api/v1/status/<model> -> the sketch-status JSON sidecar."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the sketch-status sidecar, or 404."""
        _stream(self, self._catalog.resolve_status(unquote(args[0])),
                "application/json", "no sketch status for model")
