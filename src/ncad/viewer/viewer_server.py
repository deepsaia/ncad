"""A tiny HTTP server that serves the browser 3D viewer and its glTF models.

Uses only the standard library, so it runs anywhere Python does — no extra installs,
which is the point (viewing models on machines without CAD/GL software). Routes:

- ``GET /``            -> the viewer single-page app (HTML)
- ``GET /api/models``  -> JSON list of available models
- ``GET /models/<name>`` -> the model bytes (path-traversal safe, via ModelCatalog)
"""

import json
import logging
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from ncad.viewer.model_catalog import ModelCatalog
from ncad.viewer.viewer_page import render_viewer_page

logger = logging.getLogger(__name__)

_MODEL_ROUTE = "/models/"
_BOM_ROUTE = "/api/bom/"
_PLAN_ROUTE = "/api/plan/"
_CONTENT_TYPES = {
    ".gltf": "model/gltf+json",
    ".glb": "model/gltf-binary",
    ".bin": "application/octet-stream",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def _content_type_for(path: str) -> str:
    """MIME type for a served model file, by extension."""
    lowered = path.lower()
    for extension, content_type in _CONTENT_TYPES.items():
        if lowered.endswith(extension):
            return content_type
    return "application/octet-stream"


class _ViewerRequestHandler(BaseHTTPRequestHandler):
    """Handles viewer routes. Constructed per request with an injected catalog."""

    def __init__(self, *args, catalog: ModelCatalog, **kwargs) -> None:
        self._catalog = catalog
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802 (name fixed by BaseHTTPRequestHandler)
        path = self.path.split("?", 1)[0]  # ignore any query string for routing
        if path == "/" or path == "/index.html":
            self._send_index()
        elif path == "/api/models":
            self._send_model_list()
        elif path.startswith(_BOM_ROUTE):
            self._send_bom(path[len(_BOM_ROUTE) :])
        elif path.startswith(_PLAN_ROUTE):
            self._send_plan(path[len(_PLAN_ROUTE) :])
        elif path.startswith(_MODEL_ROUTE):
            self._send_model(path[len(_MODEL_ROUTE) :])
        else:
            self.send_error(404, "not found")

    def _send_index(self) -> None:
        self._send_bytes(200, "text/html; charset=utf-8", render_viewer_page().encode("utf-8"))

    def _send_model_list(self) -> None:
        payload = json.dumps({"models": self._catalog.model_names()}).encode("utf-8")
        self._send_bytes(200, "application/json", payload)

    def _send_model(self, name: str) -> None:
        resolved = self._catalog.resolve(unquote(name))
        if resolved is None:
            self.send_error(404, "unknown model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, _content_type_for(resolved), handle.read())

    def _send_bom(self, model_name: str) -> None:
        resolved = self._catalog.resolve_bom(unquote(model_name))
        if resolved is None:
            self.send_error(404, "no BOM for model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_plan(self, model_name: str) -> None:
        resolved = self._catalog.resolve_plan(unquote(model_name))
        if resolved is None:
            self.send_error(404, "no plan for model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "image/svg+xml; charset=utf-8", handle.read())

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        logger.debug("viewer %s - %s", self.address_string(), fmt % args)


class ViewerServer:
    """Serves the browser 3D viewer for models in a directory."""

    def __init__(self, models_dir: str, host: str = "127.0.0.1", port: int = 8000) -> None:
        """:param models_dir: Directory of glTF/GLB models to serve.
        :param host: Bind address.
        :param port: Bind port; 0 picks an ephemeral free port.
        """
        catalog = ModelCatalog(models_dir)
        handler = partial(_ViewerRequestHandler, catalog=catalog)
        self._httpd = ThreadingHTTPServer((host, port), handler)
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        """The base URL the server is bound to (with the actual, possibly ephemeral port)."""
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> None:
        """Start serving in a background thread."""
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info("viewer server running at %s", self.base_url)

    def serve_forever(self) -> None:
        """Serve in the foreground until interrupted (for CLI use)."""
        logger.info("viewer server running at %s", self.base_url)
        self._httpd.serve_forever()

    def stop(self) -> None:
        """Stop the server and release the socket."""
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
