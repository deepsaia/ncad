"""Dev-only server-side hot-reload: wire tornado.autoreload so source edits re-exec the service.

``tornado.autoreload.start()`` already watches every imported ``.py`` and re-execs the same process
on change (the socket rebinds, state is fresh), which is exactly the server-code reload we want. We
deliberately do NOT ``watch()`` directories or the viewer HTML: ``watch()`` polls a single file's
mtime (not a directory tree), so watching example dirs catches nothing useful and duplicates
SpecCatalog's per-request re-scan, and watching the viewer HTML would re-exec on edits that
ViewerPage(dev=True)'s per-request re-read already surfaces. One class; the autoreload module is
injected so it is testable without a real re-exec.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ReloadWatcher:
    """Enables tornado.autoreload when running in dev; a no-op otherwise."""

    def __init__(self, dev: bool) -> None:
        """:param dev: When True, ``enable`` starts autoreload; otherwise ``enable`` is a no-op."""
        self._dev = dev

    def enable(self, autoreload: Any | None = None) -> None:
        """Start tornado.autoreload if in dev mode. Import the real module lazily by default.

        :param autoreload: The autoreload module (or a fake, in tests). Defaults to
            ``tornado.autoreload`` so callers just call ``enable()``.
        """
        if not self._dev:
            return
        if autoreload is None:
            import tornado.autoreload as autoreload
        autoreload.start()
        logger.info("server-side autoreload enabled (watching imported source modules)")
