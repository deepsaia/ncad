"""The ncad Tornado HTTP service: a versioned JSON API plus the viewer SPA under /viewer.

Owns the Tornado Application and its IOLoop. Like the stdlib ViewerServer it injects the existing
collaborators (ModelCatalog, SpecCatalog, BuildService, ViewerPage) so no business logic moves;
handlers are thin transport over those units. ``start()`` runs the IOLoop in a background thread
(each Tornado IOLoop is thread-local, so the loop is created inside that thread); ``serve_forever``
runs it in the foreground for CLI use. A per-instance ``boot_id`` (uuid4) backs the live-reload
reconnect-and-compare. Server-side autoreload (dev) is wired by ReloadWatcher.
"""

import asyncio
import logging
import threading
import uuid

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from ncad.service.access_logger import AccessLogger
from ncad.service.api_router import ApiRouter
from ncad.service.reload_watcher import ReloadWatcher
from ncad.viewer.model_catalog import ModelCatalog
from ncad.viewer.spec_catalog import SpecCatalog
from ncad.viewer.viewer_page import ViewerPage
from ncad.viewer.viewer_server import BuildServiceFactory

logger = logging.getLogger(__name__)


class NcadService:
    """Serves the ncad JSON API + viewer SPA over Tornado."""

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
        """:param models_dir: Directory of glTF/GLB models + assembly/motion sidecars to serve.
        :param host: Bind address.
        :param port: Bind port; 0 picks an ephemeral free port.
        :param examples_dir: Directory of example specs (spec panel empty if None).
        :param build_service: Injected BuildService; a default is built if None.
        :param dev: When True, hot-reload affordances are enabled (autoreload + live-reload + the
            viewer HTML is re-read per request).
        """
        self._host = host
        self._port = port
        self._dev = dev
        self._boot_id = uuid.uuid4().hex
        self._deps = make_deps(models_dir, examples_dir, dev, self._boot_id,
                               build_service=build_service)
        # A custom access log_function colors the status by class (see AccessLogger); it emits
        # through the "tornado.access" logger, which ServiceLogging configures for the CLI.
        self._app = Application(ApiRouter().rules(self._deps),
                                log_function=AccessLogger().log)
        self._server: HTTPServer | None = None
        self._ioloop: IOLoop | None = None
        self._thread: threading.Thread | None = None
        self._bound_port: int | None = None
        self._ready = threading.Event()

    @property
    def boot_id(self) -> str:
        """The per-instance boot id (uuid4 hex), used by live-reload reconnect-and-compare."""
        return self._boot_id

    @property
    def base_url(self) -> str:
        """The base URL the server is bound to (with the actual, possibly ephemeral, port)."""
        port = self._bound_port if self._bound_port is not None else self._port
        return f"http://{self._host}:{port}"

    def start(self) -> None:
        """Start serving on a background thread; block until the socket is bound."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError("ncad service did not bind within 10s")
        # _run logs "ncad service running at ..." once the socket is bound (before _ready is set),
        # so no second line here.

    def serve_forever(self) -> None:
        """Run the IOLoop in the foreground until interrupted (for CLI use)."""
        self._run()

    def _run(self) -> None:
        """Create a thread-local IOLoop, bind the server, and run the loop."""
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._ioloop = IOLoop.current()
        self._server = HTTPServer(self._app)
        sockets = _bind_sockets(self._host, self._port)
        self._bound_port = sockets[0].getsockname()[1]
        self._server.add_sockets(sockets)
        # Server-side hot-reload (dev only): start autoreload on this IOLoop so a source edit
        # re-execs the process. A no-op when dev is False (see ReloadWatcher for why it is guarded).
        ReloadWatcher(self._dev).enable()
        logger.info("ncad service running at %s", self.base_url)
        self._ready.set()
        self._ioloop.start()

    def stop(self) -> None:
        """Stop the server and its IOLoop, releasing the socket."""
        if self._ioloop is not None:
            self._ioloop.add_callback(self._shutdown)
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _shutdown(self) -> None:
        """Stop the HTTP server and the IOLoop (runs on the loop thread)."""
        if self._server is not None:
            self._server.stop()
        if self._ioloop is not None:
            self._ioloop.stop()


def _bind_sockets(host: str, port: int):
    """Bind listening sockets for ``host:port`` (port 0 = ephemeral). Kept a top-level helper."""
    from tornado.netutil import bind_sockets

    return bind_sockets(port, address=host)


def make_deps(models_dir: str, examples_dir: str | None, dev: bool, boot_id: str,
              *, build_service=None) -> dict:
    """Build the injected-collaborators dict passed to every handler's ``initialize``.

    Kept a top-level factory so tests can construct the same deps an NcadService uses (and build a
    bare Tornado Application from ApiRouter) without spinning up the full service lifecycle.
    """
    if build_service is None:
        build_service = BuildServiceFactory().create(examples_dir or "", models_dir)
    return {
        "catalog": ModelCatalog(models_dir),
        "spec_catalog": SpecCatalog(examples_dir or ""),
        "build_service": build_service,
        "page": ViewerPage(dev=dev),
        "dev": dev,
        "boot_id": boot_id,
    }
