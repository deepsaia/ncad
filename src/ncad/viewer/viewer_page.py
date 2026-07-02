"""The viewer single-page app (HTML + Three.js), rendered by :class:`ViewerPage`.

The page markup lives in the sibling ``viewer_page.html`` asset so it can be edited and
hot-reloaded without touching Python. Three.js is loaded from a CDN via an import map,
so there is no Node/npm build step; the viewer runs on any machine with a browser.

In ``dev=True`` mode the file is re-read on every render, so editing the HTML and
refreshing the browser is enough to see changes (no server restart). In the default
(production) mode the file is read once and cached.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PAGE_PATH = Path(__file__).resolve().parent / "viewer_page.html"


class ViewerPage:
    """Renders the viewer single-page app (HTML + Three.js) as a string."""

    def __init__(self, dev: bool = False) -> None:
        """:param dev: When True, re-read the HTML asset on every render (hot reload)."""
        self._dev = dev
        self._cached: str | None = None

    def render(self) -> str:
        """Return the viewer single-page app as an HTML string."""
        if self._dev:
            return self._read()
        if self._cached is None:
            self._cached = self._read()
        return self._cached

    @staticmethod
    def _read() -> str:
        """Read the HTML asset from disk."""
        return _PAGE_PATH.read_text(encoding="utf-8")
