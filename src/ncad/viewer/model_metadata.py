"""Read and write a model's metadata sidecar (``out/<stem>.meta.json``).

The sidecar records how a model was built (its source spec and the tool/kernel
versions) so the viewer can regenerate it later by rebuilding that source.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_META_SUFFIX = ".meta.json"


class ModelMetadata:
    """Reads and writes ``<stem>.meta.json`` beside a model in one directory."""

    def __init__(self, models_dir: str) -> None:
        """:param models_dir: Directory holding the models and their meta sidecars."""
        self._directory = os.path.abspath(models_dir)

    def write(
        self,
        model_name: str,
        source: str,
        built_at: str,
        ncad_version: str,
        kernel_version: str,
    ) -> str:
        """Write the meta sidecar for ``model_name`` and return its path."""
        stem = os.path.splitext(model_name)[0]
        path = os.path.join(self._directory, stem + _META_SUFFIX)
        payload = {
            "source": source,
            "built_at": built_at,
            "ncad_version": ncad_version,
            "kernel_version": kernel_version,
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        logger.debug("wrote meta sidecar %s", path)
        return path

    def read(self, model_name: str) -> dict | None:
        """Read the meta sidecar for ``model_name``, or None if absent/unreadable."""
        stem = os.path.splitext(model_name)[0]
        path = os.path.join(self._directory, stem + _META_SUFFIX)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            logger.warning("could not read meta sidecar %s", path)
            return None
