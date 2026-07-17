"""Serve the viewer SPA at /viewer (with a dev bootstrap block) and redirect / to it.

``ViewerHandler`` renders the existing ``ViewerPage`` HTML and injects a tiny bootstrap script
carrying ``window.NCAD_DEV`` and ``window.NCAD_BOOT_ID`` so the SPA can decide whether to open the
live-reload socket and detect a server restart. ``ViewerPage`` itself stays argument-free; the
injection is the one intentional deviation from "used exactly as today". ``RootRedirectHandler``
302-redirects / to /viewer.
"""

import json

from tornado.web import RequestHandler

from ncad.service.base_handler import BaseApiHandler

_HEAD_TAG = "<head>"


def _bootstrap_script(dev: bool, boot_id: str) -> str:
    """The bootstrap <script> injected right after <head>, exposing the dev flag + boot id."""
    return ("<script>"
            f"window.NCAD_DEV={json.dumps(bool(dev))};"
            f"window.NCAD_BOOT_ID={json.dumps(boot_id)};"
            f'window.NCAD_API_BASE="/api/v1";'
            "</script>")


def _inject(html: str, dev: bool, boot_id: str) -> str:
    """Insert the bootstrap script right after the first <head> tag (or prepend if absent)."""
    script = _bootstrap_script(dev, boot_id)
    index = html.find(_HEAD_TAG)
    if index == -1:
        return script + html
    cut = index + len(_HEAD_TAG)
    return html[:cut] + script + html[cut:]


class ViewerHandler(BaseApiHandler):
    """GET /viewer (and /viewer/<deep-link>) -> the SPA HTML with the dev bootstrap injected."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Render the viewer page and inject the bootstrap block. Any deep-link tail is ignored
        here (the SPA reads it from the URL path itself)."""
        html = _inject(self._page.render(), self._dev, self._boot_id)
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.safe_finish(html)


class RootRedirectHandler(RequestHandler):
    """GET / -> 302 redirect to /viewer."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Redirect to the viewer mount point (302, not permanent)."""
        self.redirect("/viewer", permanent=False)
