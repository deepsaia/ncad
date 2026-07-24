"""Read and write a model's sketch-status sidecar (``out/<stem>.status.json``).

Records each sketch feature's constraint status (well/under/over/inconsistent + dof +
failing-constraint ids) so the viewer and later tools can surface it. Mirrors
ModelMetadata: best-effort IO, a missing/unreadable sidecar reads as None, never blocks
the build.
"""

import json
import logging
from pathlib import Path

from ncad.ops.sketch_status import SketchStatus

logger = logging.getLogger(__name__)

_STATUS_SUFFIX = ".status.json"


class SketchStatusSidecar:
    """Reads and writes ``<stem>.status.json`` beside a model in one directory."""

    def __init__(self, models_dir: str) -> None:
        """:param models_dir: Directory holding the models and their status sidecars."""
        self._directory = Path(models_dir).absolute()

    def write(self, model_name: str, statuses: list[SketchStatus]) -> str:
        """Write the status sidecar for ``model_name`` and return its path."""
        path = self._directory / (Path(model_name).stem + _STATUS_SUFFIX)
        payload = {"sketches": [s.to_dict() for s in statuses]}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        logger.debug("wrote status sidecar %s", path)
        return str(path)

    def read(self, model_name: str) -> dict | None:
        """Read the status sidecar for ``model_name``, or None if absent/unreadable."""
        path = self._directory / (Path(model_name).stem + _STATUS_SUFFIX)
        if not path.is_file():
            return None
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            logger.warning("could not read status sidecar %s", path)
            return None
