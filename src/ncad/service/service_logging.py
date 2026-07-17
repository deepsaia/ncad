"""Colored, timestamped terminal logging for the long-running ncad service.

Uses rich's ``RichHandler`` (rich ships with typer, no new dependency): it colors the level column
and aligns messages, and we give it a time column showing the date + time to the millisecond
(``YYYY-MM-DD HH:MM:SS.mmm``). One class configures the root logger + Tornado's access logger so
both the service's own lines and per-request access lines are colored and stamped alike.
"""

import logging
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

# rich's default log time style is dim cyan, which washes out on dark terminals. Override the
# "log.time" style to a bright (non-dim) cyan so the date-time column stays readable on any
# background.
_THEME = Theme({"log.time": "bold cyan"})


def _format_time(moment: datetime) -> Text:
    """Render a log time as ``YYYY-MM-DD HH:MM:SS.mmm`` (date + time, millisecond precision)."""
    millis = moment.microsecond // 1000  # 0..999
    return Text(f"{moment:%Y-%m-%d %H:%M:%S}.{millis:03d}")


class ServiceLogging:
    """Installs a rich, colored, date-time (ms) log handler on the root + the tornado.access log."""

    def install(self, level: int = logging.INFO) -> None:
        """Replace the root handlers with a single RichHandler and set INFO on tornado.access."""
        handler = RichHandler(
            console=Console(theme=_THEME),
            show_time=True,
            show_level=True,
            show_path=False,
            omit_repeated_times=False,
            log_time_format=_format_time,
            rich_tracebacks=True,
        )
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)
        logging.getLogger("tornado.access").setLevel(logging.INFO)
