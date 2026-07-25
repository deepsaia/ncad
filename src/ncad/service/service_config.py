"""Typed reads of the ``NCAD_*`` service env knobs, with defaults, in one place.

Mirrors the existing ``NCAD_CCX`` convention (plain ``os.environ.get``, no dotenv dependency).
CLI flags override these (flag > env > default); see viewer_cli.serve. One class.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    """Resolved ``ncad serve`` configuration (server bind + build-concurrency knobs)."""

    host: str
    port: int
    dev: bool
    max_workers: int
    max_concurrent_builds: int
    job_queue_max: int
    job_ttl_s: float
    job_poll_ms: int
    shutdown_timeout_s: float
    jobs_dir: str | None

    @staticmethod
    def worker_default() -> int:
        """Default process-pool size for a local single-user viewer.

        Capped at 4: each spawn worker imports OCP/OCCT (a heavy, few-hundred-MB resident process),
        so sizing to every core would risk multi-GB memory under load for a benefit one interactive
        user rarely needs. Still bounded below the core count (leave 2 for the loop + OS). A heavy
        server can opt up via NCAD_MAX_WORKERS.
        """
        return max(1, min(4, (os.cpu_count() or 2) - 2))

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        """Read every ``NCAD_*`` knob from the environment, applying defaults for blanks."""
        max_workers = _int_env("NCAD_MAX_WORKERS", cls.worker_default())
        return cls(
            host=os.environ.get("NCAD_HOST") or "127.0.0.1",
            port=_int_env("NCAD_PORT", 8000),
            dev=_bool_env("NCAD_DEV", False),
            max_workers=max_workers,
            max_concurrent_builds=_int_env("NCAD_MAX_CONCURRENT_BUILDS", max_workers),
            job_queue_max=_int_env("NCAD_JOB_QUEUE_MAX", 32),
            job_ttl_s=_float_env("NCAD_JOB_TTL", 300.0),
            job_poll_ms=_int_env("NCAD_JOB_POLL_MS", 400),
            shutdown_timeout_s=_float_env("NCAD_SHUTDOWN_TIMEOUT", 30.0),
            jobs_dir=(os.environ.get("NCAD_JOBS_DIR") or None),
        )


_TRUE = {"1", "true", "yes", "on"}


def _bool_env(key: str, default: bool) -> bool:
    """Parse a boolean env var (``1/true/yes/on`` truthy); blank/unset -> ``default``."""
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in _TRUE


def _int_env(key: str, default: int) -> int:
    """Parse an int env var; blank/unset/invalid -> ``default``."""
    raw = os.environ.get(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(key: str, default: float) -> float:
    """Parse a float env var; blank/unset/invalid -> ``default``."""
    raw = os.environ.get(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default
