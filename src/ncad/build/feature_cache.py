"""An in-memory cache of built feature shapes and their element descriptors.

Held on a DocumentBuilder for its lifetime (design decision: in-memory, per-instance).
Keyed by the content-addressed cache key (see cache_key.py); a hit restores both the
shape and the cached describe_elements output so the executor skips the op and the
kernel describe call entirely. Also records per-run hit/miss stats per feature id for
the incremental-rebuild demo and gate. Never consulted across kernel versions (the
version is baked into the key), so a stale hit is structurally impossible.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheEntry:
    """A cached feature result: the built shape and its element descriptors."""

    shape: Any
    descriptors: list | None


class FeatureCache:
    """In-memory feature-result cache with per-run hit/miss stats."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._stats: dict[str, bool] = {}

    def get(self, key: str) -> CacheEntry | None:
        """The entry for ``key``, or None."""
        return self._entries.get(key)

    def put(self, key: str, entry: CacheEntry) -> None:
        """Store ``entry`` under ``key``."""
        self._entries[key] = entry

    def record(self, feature_id: str, hit: bool) -> None:
        """Record whether ``feature_id`` was a cache hit on the current run."""
        self._stats[feature_id] = hit

    def stats(self) -> dict[str, bool]:
        """Feature-id -> was-hit for the current run."""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """Clear the per-run stats (entries are kept)."""
        self._stats = {}
