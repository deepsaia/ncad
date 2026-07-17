"""Shared base for the ncad JSON API handlers: dependency injection + a uniform error envelope.

Every API handler receives the same injected collaborators (the model/spec catalogs, the build
service, the viewer page, and the service dev flag + boot id) through Tornado's ``initialize``,
populated from the route table. The base also centralizes the JSON write helper and the
``{"error": ...}`` envelope so the 400/404/500 contract matches the stdlib server exactly, and it
finishes responses through a ``StreamClosedError``-safe path (a client that hangs up mid-write must
not raise), plus a CORS preflight hook for a future cross-origin (React) client. These mirror the
neuro-san Tornado service idioms (BaseRequestHandler.do_finish / options).
"""

import json
import logging
from typing import Any

from tornado.iostream import StreamClosedError
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

    def set_default_headers(self) -> None:
        """Permit cross-origin API use (a future React client on another origin).

        A local dev tool, not an authenticated service, so ``*`` is fine. Applied to every response
        (Tornado calls this before each request) so both the JSON routes and the preflight agree.
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self, *args: str, **kwargs: str) -> None:
        """Answer a CORS preflight with 204 No Content (headers set in set_default_headers)."""
        self.set_status(204)
        self.safe_finish()

    def safe_finish(self, chunk: str | bytes | None = None) -> None:
        """finish() that swallows a client-hung-up mid-write instead of raising to the loop."""
        try:
            self.finish(chunk)
        except StreamClosedError:
            logger.warning("client closed the connection before the response finished")

    def write_json(self, status: int, payload: dict) -> None:
        """Write ``payload`` as a JSON response with ``status`` (stream-close safe)."""
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.safe_finish(json.dumps(payload))

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
