"""Unit tests for the service's colored terminal logging helpers.

Covers the status-class color mapping (AccessLogger) and the millisecond time format
(ServiceLogging), which drive the ncad serve terminal output.
"""

from datetime import datetime

from ncad.service.access_logger import _status_style
from ncad.service.service_logging import _format_time


def test_status_style_by_class():
    assert _status_style(200) == "bold green"
    assert _status_style(204) == "bold green"
    assert _status_style(302) == "bold cyan"
    assert _status_style(404) == "bold yellow"
    assert _status_style(400) == "bold yellow"
    assert _status_style(500) == "bold red"
    assert _status_style(503) == "bold red"


def test_format_time_millisecond_precision():
    moment = datetime(2026, 7, 17, 21, 3, 23, 467000)
    assert str(_format_time(moment)) == "2026-07-17 21:03:23.467"


def test_format_time_pads_millis():
    moment = datetime(2026, 1, 2, 3, 4, 5, 9000)  # 9 ms -> "009"
    assert str(_format_time(moment)) == "2026-01-02 03:04:05.009"
