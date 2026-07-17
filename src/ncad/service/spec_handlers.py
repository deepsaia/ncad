"""The example-spec tree handler: GET /api/v1/specs."""

from ncad.service.base_handler import BaseApiHandler


class SpecsHandler(BaseApiHandler):
    """GET /api/v1/specs -> the nested tree of example spec documents."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"tree": [...]}`` from the injected SpecCatalog."""
        self.write_json(200, {"tree": self._spec_catalog.tree()})
