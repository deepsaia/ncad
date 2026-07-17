"""Shared base for the ncad JSON API handlers: dependency injection + a uniform error envelope.

Every API handler receives the same injected collaborators (the model/spec catalogs, the build
service, the viewer page, and the service dev flag + boot id) through Tornado's ``initialize``,
populated from the route table. The base also centralizes the JSON write helper and the
``{"error": ...}`` envelope so the 400/404/500 contract matches the stdlib server exactly.
"""

import json
import logging
from typing import Any

from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


class BaseApiHandler(RequestHandler):
    """Base RequestHandler carrying the injected ncad collaborators and JSON helpers."""

    def initialize(self, **kwargs: Any) -> None:
        """Store the injected collaborators (called by Tornado per request from the route table).

        Uses ``**kwargs`` (a compatible widening of RequestHandler.initialize) so the required
        collaborators - catalog, spec_catalog, build_service, page, dev, boot_id - are read from
        the route-table dict without narrowing the base signature.
        """
        self._catalog = kwargs["catalog"]
        self._spec_catalog = kwargs["spec_catalog"]
        self._build_service = kwargs["build_service"]
        self._page = kwargs["page"]
        self._dev: bool = kwargs["dev"]
        self._boot_id: str = kwargs["boot_id"]

    def write_json(self, status: int, payload: dict) -> None:
        """Write ``payload`` as a JSON response with ``status``."""
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(payload))

    def write_error_json(self, status: int, message: str) -> None:
        """Write the shared ``{"error": message}`` envelope with ``status``."""
        self.write_json(status, {"error": message})

    def load_spec_body(self) -> str | None:
        """Parse the request body as JSON and return its ``spec`` field, or None if malformed.

        A malformed body / missing field is a client error: the caller sends 400. Kept here so
        every POST handler shares one parse + validation path (matches the stdlib server).
        """
        try:
            body = json.loads(self.request.body or b"{}")
            return body["spec"]
        except (ValueError, KeyError, TypeError):
            return None
