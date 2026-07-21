"""A tiny HTTP server that serves the browser 3D viewer and its glTF models.

Uses only the standard library, so it runs anywhere Python does, no extra installs,
which is the point (viewing models on machines without CAD/GL software). Routes:

- ``GET /``            -> the viewer single-page app (HTML)
- ``GET /api/specs``   -> JSON tree of example specs
- ``GET /api/models``  -> JSON list of available models (with recorded source)
- ``GET /models/<name>`` -> the model bytes (path-traversal safe, via ModelCatalog)
- ``POST /api/build``  -> build a spec (JSON body ``{"spec": ...}``)
- ``POST /api/models/<name>/delete`` -> delete a model and its sidecars
"""

import json
import logging
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from ncad.viewer.build_service import BuildError
from ncad.viewer.model_catalog import ModelCatalog
from ncad.viewer.spec_catalog import SpecCatalog
from ncad.viewer.viewer_page import ViewerPage

logger = logging.getLogger(__name__)

_MODEL_ROUTE = "/models/"
_API_MODELS_ROUTE = "/api/models/"
_BOM_ROUTE = "/api/bom/"
_PLAN_ROUTE = "/api/plan/"
_ELEMENTMAP_ROUTE = "/api/elementmap/"
_HIERARCHY_ROUTE = "/api/hierarchy/"
_STATUS_ROUTE = "/api/status/"
_ASSEMBLY_ROUTE = "/api/assembly/"
_MOTION_ROUTE = "/api/motion/"
_ROBOT_ROUTE = "/api/robot/"
_ROBOT_SWEEPS_ROUTE = "/api/robot-sweeps/"
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

    def __init__(
        self,
        *args,
        catalog: ModelCatalog,
        spec_catalog: SpecCatalog,
        build_service,
        page: ViewerPage,
        **kwargs,
    ) -> None:
        self._catalog = catalog
        self._spec_catalog = spec_catalog
        self._build_service = build_service
        self._page = page
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802 (name fixed by BaseHTTPRequestHandler)
        path = self.path.split("?", 1)[0]  # ignore any query string for routing
        if path == "/" or path == "/index.html":
            self._send_index()
        elif path == "/api/specs":
            self._send_json(200, {"tree": self._spec_catalog.tree()})
        elif path == "/api/models":
            self._send_model_list()
        elif path == "/api/assemblies":
            self._send_json(200, {"assemblies": self._catalog.assembly_names()})
        elif path == "/api/motions":
            self._send_json(200, {"motions": self._catalog.motion_names()})
        elif path == "/api/robots":
            self._send_json(200, {"robots": self._catalog.robots_with_labels()})
        elif path.startswith(_ROBOT_SWEEPS_ROUTE):
            self._send_robot_sweeps(path[len(_ROBOT_SWEEPS_ROUTE) :])
        elif path.startswith(_ROBOT_ROUTE):
            self._send_robot(path[len(_ROBOT_ROUTE) :])
        elif path.startswith(_MOTION_ROUTE):
            self._send_motion(path[len(_MOTION_ROUTE) :])
        elif path.startswith(_ASSEMBLY_ROUTE):
            self._send_assembly(path[len(_ASSEMBLY_ROUTE) :])
        elif path.startswith(_BOM_ROUTE):
            self._send_bom(path[len(_BOM_ROUTE) :])
        elif path.startswith(_PLAN_ROUTE):
            self._send_plan(path[len(_PLAN_ROUTE) :])
        elif path.startswith(_ELEMENTMAP_ROUTE):
            self._send_elementmap(path[len(_ELEMENTMAP_ROUTE) :])
        elif path.startswith(_HIERARCHY_ROUTE):
            self._send_hierarchy(path[len(_HIERARCHY_ROUTE) :])
        elif path.startswith(_STATUS_ROUTE):
            self._send_status(path[len(_STATUS_ROUTE) :])
        elif path.startswith(_MODEL_ROUTE):
            self._send_model(path[len(_MODEL_ROUTE) :])
        elif self._catalog.resolve(unquote(path.lstrip("/"))) is not None:
            # Deep link: /<model>.glb serves the SPA, which preselects that model from the
            # URL path. (Model bytes are still fetched via /models/<name>.)
            self._send_index()
        else:
            self.send_error(404, "not found")

    def _send_index(self) -> None:
        self._send_bytes(200, "text/html; charset=utf-8", self._page.render().encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802 (name fixed by BaseHTTPRequestHandler)
        path = self.path.split("?", 1)[0]
        if path == "/api/build":
            self._handle_build()
        elif path == "/api/assemble":
            self._handle_assemble()
        elif path == "/api/motion-build":
            self._handle_motion_build()
        elif path.startswith(_API_MODELS_ROUTE) and path.endswith("/delete"):
            name = path[len(_API_MODELS_ROUTE) : -len("/delete")]
            self._handle_delete(unquote(name))
        elif path.startswith(_ASSEMBLY_ROUTE) and path.endswith("/delete"):
            name = path[len(_ASSEMBLY_ROUTE) : -len("/delete")]
            self._handle_delete_assembly(unquote(name))
        else:
            self.send_error(404, "not found")

    def _handle_build(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            spec = body["spec"]
        except (ValueError, KeyError):
            self._send_json(400, {"error": "request must be JSON with a 'spec' field"})
            return
        try:
            result = self._build_service.build(spec)
        except BuildError as exc:
            logger.warning("build rejected for %s: %s", spec, exc)
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected build failure for %s", spec)
            self._send_json(500, {"error": "internal build error"})
            return
        self._send_json(200, {"models": self._catalog.models_with_sources(), **result})

    def _handle_assemble(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            spec = body["spec"]
        except (ValueError, KeyError):
            self._send_json(400, {"error": "request must be JSON with a 'spec' field"})
            return
        try:
            result = self._build_service.assemble(spec)
        except BuildError as exc:
            logger.warning("assemble rejected for %s: %s", spec, exc)
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected assemble failure for %s", spec)
            self._send_json(500, {"error": "internal assemble error"})
            return
        self._send_json(200, {"assemblies": self._catalog.assembly_names(), **result})

    def _handle_motion_build(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            spec = body["spec"]
        except (ValueError, KeyError):
            self._send_json(400, {"error": "request must be JSON with a 'spec' field"})
            return
        try:
            result = self._build_service.build_motion(spec)
        except BuildError as exc:
            logger.warning("motion-build rejected for %s: %s", spec, exc)
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected motion-build failure for %s", spec)
            self._send_json(500, {"error": "internal motion-build error"})
            return
        self._send_json(200, {"motions": self._catalog.motion_names(), **result})

    def _handle_delete(self, name: str) -> None:
        removed = self._catalog.delete_model(name)
        if removed is None:
            logger.warning("delete rejected: unknown model %r", name)
            self.send_error(404, "unknown model")
            return
        logger.info("deleted model %s", name)
        self._send_json(200, {"models": self._catalog.models_with_sources()})

    def _handle_delete_assembly(self, name: str) -> None:
        removed = self._catalog.delete_assembly(name)
        if removed is None:
            logger.warning("delete rejected: unknown assembly %r", name)
            self.send_error(404, "unknown assembly")
            return
        logger.info("deleted assembly %s", name)
        self._send_json(200, {"assemblies": self._catalog.assembly_names()})

    def _send_model_list(self) -> None:
        self._send_json(200, {"models": self._catalog.models_with_sources()})

    def _send_json(self, status: int, payload: dict) -> None:
        self._send_bytes(status, "application/json", json.dumps(payload).encode("utf-8"))

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

    def _send_elementmap(self, model_name: str) -> None:
        resolved = self._catalog.resolve_elementmap(unquote(model_name))
        if resolved is None:
            self.send_error(404, "no element map for model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_hierarchy(self, model_name: str) -> None:
        resolved = self._catalog.resolve_hierarchy(unquote(model_name))
        if resolved is None:
            self.send_error(404, "no hierarchy for model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_status(self, model_name: str) -> None:
        resolved = self._catalog.resolve_status(unquote(model_name))
        if resolved is None:
            self.send_error(404, "no sketch status for model")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_assembly(self, name: str) -> None:
        resolved = self._catalog.resolve_assembly(unquote(name))
        if resolved is None:
            self.send_error(404, "unknown assembly")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_motion(self, name: str) -> None:
        resolved = self._catalog.resolve_motion(unquote(name))
        if resolved is None:
            self.send_error(404, "no motion for assembly")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_robot(self, name: str) -> None:
        resolved = self._catalog.resolve_robot(unquote(name))
        if resolved is None:
            self.send_error(404, "unknown robot")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_robot_sweeps(self, name: str) -> None:
        resolved = self._catalog.resolve_robot_sweeps(unquote(name))
        if resolved is None:
            self.send_error(404, "no sweeps for robot")
            return
        with open(resolved, "rb") as handle:
            self._send_bytes(200, "application/json", handle.read())

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (name fixed by base class)
        logger.debug("viewer %s - %s", self.address_string(), format % args)


class BuildServiceFactory:
    """Builds the production BuildService, importing the kernel lazily.

    Kept a class (not module functions) so this module has no class-less globals; the
    kernel imports happen inside methods so constructing the viewer never pays the OCP
    cost unless a build is actually requested.
    """

    def create(self, examples_dir: str, models_dir: str):
        """Construct a BuildService wired to the real DocumentBuilder + build123d kernel."""
        from ncad.viewer.build_service import BuildService

        return BuildService(
            examples_dir,
            models_dir,
            builder_factory=self._make_builder,
            clock=self._utc_now_iso,
            versions={"ncad": self._ncad_version(), "kernel": "build123d"},
        )

    @staticmethod
    def _make_builder():
        """Zero-arg factory for the production DocumentBuilder (imports the kernel)."""
        from ncad.build.document_builder import DocumentBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        return DocumentBuilder(Build123dKernel())

    @staticmethod
    def _utc_now_iso() -> str:
        """Current UTC time as an ISO-8601 string."""
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()

    @staticmethod
    def _ncad_version() -> str:
        """Installed ncad version, or 'unknown' if metadata is unavailable."""
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("ncad")
        except PackageNotFoundError:
            return "unknown"


class ViewerServer:
    """Serves the browser 3D viewer for models in a directory."""

    def __init__(
        self,
        models_dir: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        *,
        examples_dir: str | None = None,
        build_service=None,
        dev: bool = False,
    ) -> None:
        """:param models_dir: Directory of glTF/GLB models to serve.
        :param host: Bind address.
        :param port: Bind port; 0 picks an ephemeral free port.
        :param examples_dir: Directory of example specs (spec panel empty if None).
        :param build_service: Injected BuildService; a default is built if None.
        :param dev: When True, re-read the viewer HTML per request (hot reload).
        """
        catalog = ModelCatalog(models_dir)
        spec_catalog = SpecCatalog(examples_dir or "")
        if build_service is None:
            build_service = BuildServiceFactory().create(examples_dir or "", models_dir)
        handler = partial(
            _ViewerRequestHandler,
            catalog=catalog,
            spec_catalog=spec_catalog,
            build_service=build_service,
            page=ViewerPage(dev=dev),
        )
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
