"""Browser live-reload websocket (dev only): send the live boot id on connect.

The live-reload model is reconnect-and-compare, NOT server push. When a client connects, the
handler sends one JSON ``hello`` frame carrying this process's ``boot_id``. The SPA records the id
it first saw; when the server re-execs (autoreload), the socket drops, the SPA reconnects with
backoff, and the fresh process sends a different boot id, which triggers ``location.reload()``. The
handler therefore keeps NO client set and never pushes: it just answers each connection. Mounted
only in dev (see ApiRouter), so production never exposes it.
"""

import json
from typing import Any

from tornado.websocket import WebSocketHandler


class LiveReloadHandler(WebSocketHandler):
    """WS /ws/livereload -> emits ``{"type": "hello", "boot_id": ...}`` once on open."""

    def initialize(self, **kwargs: Any) -> None:
        """Store the live boot id (injected from the route table)."""
        self._boot_id: str = kwargs["boot_id"]

    def open(self, *args: str, **kwargs: str) -> None:
        """On connect, send the hello frame carrying this process's boot id, then stay open."""
        self.write_message(json.dumps({"type": "hello", "boot_id": self._boot_id}))

    def check_origin(self, origin: str) -> bool:
        """Allow any origin: this is a localhost dev tool, not an authenticated service."""
        return True
