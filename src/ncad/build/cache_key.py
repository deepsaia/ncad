"""Compute a feature's content-addressed cache key.

The key is a chained content hash: the pinned kernel version, the feature's own
resolved definition (parameters already inlined, reserved runtime keys removed), and
the keys of the features it depends on. Editing a parameter changes that feature's key
and, through the chained dependency keys, every downstream feature's key, so only the
dirty suffix misses the cache. Pure and deterministic: no randomness, canonical JSON.
"""

import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Runtime-only feature keys that must not affect identity (they hold resolved handles / context).
_RESERVED_KEYS = ("__refs__", "__shapes__", "__base_dir__", "__imported__")


class CacheKeyBuilder:
    """Builds chained content-hash cache keys for features."""

    def __init__(self, kernel_version: str) -> None:
        self._kernel_version = kernel_version

    def key(self, resolved_feature: dict, dep_keys: list[str]) -> str:
        """The sha256 hex key for ``resolved_feature`` given its dependency keys."""
        payload = {
            "kernel": self._kernel_version,
            "feature": _strip_reserved(resolved_feature),
            "deps": sorted(dep_keys),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _strip_reserved(feature: dict) -> dict:
    """A copy of ``feature`` without runtime-only reserved keys."""
    return {k: v for k, v in feature.items() if k not in _RESERVED_KEYS}
