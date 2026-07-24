"""Read and write a model's metadata sidecar (``out/<stem>.meta.json``).

The sidecar records how a model was built (its source spec and the tool/kernel
versions) so the viewer can regenerate it later by rebuilding that source.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_META_SUFFIX = ".meta.json"


class ModelMetadata:
    """Reads and writes ``<stem>.meta.json`` beside a model in one directory."""

    def __init__(self, models_dir: str) -> None:
        """:param models_dir: Directory holding the models and their meta sidecars."""
        self._directory = Path(models_dir).absolute()

    def write(
        self,
        model_name: str,
        source: str,
        built_at: str,
        ncad_version: str,
        kernel_version: str,
    ) -> str:
        """Write the meta sidecar for ``model_name`` and return its path."""
        path = self._directory / (Path(model_name).stem + _META_SUFFIX)
        payload = {
            "source": source,
            "built_at": built_at,
            "ncad_version": ncad_version,
            "kernel_version": kernel_version,
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        logger.debug("wrote meta sidecar %s", path)
        return str(path)

    def read(self, model_name: str) -> dict | None:
        """Read the meta sidecar for ``model_name``, or None if absent/unreadable."""
        path = self._directory / (Path(model_name).stem + _META_SUFFIX)
        if not path.is_file():
            return None
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            logger.warning("could not read meta sidecar %s", path)
            return None
