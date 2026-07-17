"""Serve the OpenAPI document at /api/v1/openapi.json."""

from typing import Any

from ncad.service.base_handler import BaseApiHandler
from ncad.service.openapi_spec import OpenApiSpec


class OpenApiHandler(BaseApiHandler):
    """GET /api/v1/openapi.json -> the hand-authored OpenAPI 3.1 document."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return the OpenAPI spec as JSON."""
        document: dict[str, Any] = OpenApiSpec().document()
        self.write_json(200, document)
