"""Resolve each body's material from the part document via its minting feature.

A body's material is its creating feature's ``material`` (the feature whose id equals
``Body.created_by``), falling back to the part-level ``material`` default. An inline
``mat_data`` on that feature deep-merges onto the referenced record. This reuses the existing
per-body provenance (``created_by``) rather than a separate binding, and keeps ``Body``
geometry-only (associative resolution over mutating identity records).
"""

import logging
from typing import Any

from ncad.spec.material_library import MaterialLibrary

logger = logging.getLogger(__name__)


class MaterialResolver:
    """Maps a body to its resolved material record via the part document."""

    def __init__(self, part: dict, library: MaterialLibrary) -> None:
        self._part = part
        self._library = library
        self._features = {f["id"]: f for f in part.get("features", []) if "id" in f}

    def material_name(self, body: Any) -> str | None:
        """The body's material name: its creating feature's, else the part default, else None."""
        feature = self._features.get(body.created_by)
        if feature is not None and "material" in feature:
            return feature["material"]
        return self._part.get("material")

    def for_body(self, body: Any) -> dict | None:
        """The resolved mat_data for ``body`` (inline mat_data override merged), or None."""
        name = self.material_name(body)
        if name is None:
            return None
        feature = self._features.get(body.created_by)
        override = feature.get("mat_data") if feature is not None else None
        return self._library.resolve(name, override=override)
