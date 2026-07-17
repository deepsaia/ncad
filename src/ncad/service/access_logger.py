"""A Tornado ``log_function`` that logs each request with a status-class-colored code.

Tornado's default access log emits a single uniform line per request. This replaces it so the HTTP
status is colored by class (2xx green, 3xx cyan, 4xx yellow, 5xx red) using rich markup, which the
service's RichHandler renders. Wired via ``Application(..., log_function=AccessLogger().log)``.
"""

import logging
from typing import Any

from rich.markup import escape

logger = logging.getLogger("tornado.access")


def _status_style(status: int) -> str:
    """rich style name for an HTTP status by class: 2xx green, 3xx cyan, 4xx yellow, 5xx red."""
    if 200 <= status < 300:
        return "bold green"
    if 300 <= status < 400:
        return "bold cyan"
    if 400 <= status < 500:
        return "bold yellow"
    return "bold red"


class AccessLogger:
    """Logs each finished request with the status colored by class (rich markup)."""

    def log(self, handler: Any) -> None:
        """Tornado ``log_function``: emit one colored access line per request.

        Chooses the log level the way Tornado does (info < 400, warning < 500, error otherwise) so
        error responses stand out in level as well as color. The status is wrapped in rich markup;
        the dynamic method/URI are escaped so a stray ``[`` in a path cannot break rendering. The
        ``markup`` record flag opts THIS record into markup, and ``highlighter=None`` turns off
        rich's default number-highlighter for this record so it cannot re-color the status digits
        (which would clobber the status-class color) - both set per-record, not globally.
        """
        status = handler.get_status()
        if status < 400:
            level = logging.INFO
        elif status < 500:
            level = logging.WARNING
        else:
            level = logging.ERROR
        request_ms = 1000.0 * handler.request.request_time()
        method = escape(handler.request.method or "")
        uri = escape(handler.request.uri or "")
        message = (f"[{_status_style(status)}]{status}[/] {method} {uri} "
                   f"({handler.request.remote_ip}) {request_ms:.1f}ms")
        logger.log(level, message, extra={"markup": True, "highlighter": None})
