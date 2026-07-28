"""A wall-clock guard for a geometry build, so a wedged OCP op fails instead of hanging forever.

OCP (the OpenCASCADE C++ kernel) has no timeout: a degenerate boolean, fillet, or tessellation can
spin indefinitely and wedge the whole build (the observed failure mode that left stale processes).
ncad's feature pipeline runs OCP as a SEQUENCE of ops in a Python loop, so a POSIX interval timer
(SIGALRM) fires between ops and raises here, bounding the build without the cost of pickling OCP
shapes across a subprocess. The motion solve has its own subprocess bound (pyondsel); this covers
the geometry side.

Limitations, stated honestly: SIGALRM only interrupts at a point where control returns to Python, so
a SINGLE monolithic OCP call longer than the bound is not interruptible (rare; the common wedge is a
many-op build). And signals are deliverable only on the main thread, so off-main-thread callers get
no guard (a warning, not a crash) - the service already isolates each build in its own process where
this runs on that process's main thread. One class.
"""

import logging
import os
import signal
import threading
from types import FrameType

logger = logging.getLogger(__name__)

# The shared wall-clock bound (seconds) for a build and for the motion solve. Generous by default
# (15 min) so a genuinely complex mechanism has room; NCAD_BUILD_TIMEOUT overrides it.
_DEFAULT_BUILD_TIMEOUT_S = 900.0


def build_timeout_s() -> float:
    """The build/solve wall-clock bound (seconds): NCAD_BUILD_TIMEOUT or the generous default.

    A malformed or non-positive value falls back to the default rather than raising, so a bad env
    var never blocks a build; it is only a safety bound on a hung op/solve.
    """
    raw = os.environ.get("NCAD_BUILD_TIMEOUT")
    if raw is None:
        return _DEFAULT_BUILD_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        logger.warning("ignoring non-numeric NCAD_BUILD_TIMEOUT=%r; using %.0fs",
                       raw, _DEFAULT_BUILD_TIMEOUT_S)
        return _DEFAULT_BUILD_TIMEOUT_S
    return value if value > 0 else _DEFAULT_BUILD_TIMEOUT_S


class BuildTimeoutError(Exception):
    """Raised when a guarded geometry build exceeds its wall-clock bound."""


class BuildTimeout:
    """Context manager: raises BuildTimeoutError if the block runs past ``seconds`` (SIGALRM)."""

    def __init__(self, seconds: float, label: str = "build") -> None:
        """:param seconds: wall-clock bound; <= 0 disables the guard (an unbounded build).
        :param label: what is being bounded, for the error message + log.
        """
        self._seconds = seconds
        self._label = label
        self._previous: object = None
        self._armed = False

    def __enter__(self) -> "BuildTimeout":
        if self._seconds <= 0:
            return self
        if threading.current_thread() is not threading.main_thread():
            # Signals only arm on the main thread; degrade to unguarded rather than raise, so a
            # threaded caller still builds (the service isolates builds in their own processes).
            logger.warning("build timeout not armed for %s: not on the main thread", self._label)
            return self
        self._previous = signal.signal(signal.SIGALRM, self._on_alarm)
        signal.setitimer(signal.ITIMER_REAL, self._seconds)
        self._armed = True
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        if self._armed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self._previous)  # type: ignore[arg-type]
            self._armed = False
        return False

    def _on_alarm(self, signum: int, frame: FrameType | None) -> None:
        raise BuildTimeoutError(
            f"{self._label} exceeded the {self._seconds:g}s build timeout "
            "(NCAD_BUILD_TIMEOUT); the geometry op likely wedged")
