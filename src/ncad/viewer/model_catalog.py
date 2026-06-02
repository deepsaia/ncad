"""Discover 3D model files (glTF/GLB) in a directory for the browser viewer.

Keeps filesystem concerns out of the HTTP server: the server asks the catalog what
models exist and resolves a requested name to a safe absolute path (rejecting anything
outside the directory, so a crafted name can't escape via ``..``).
"""

import logging
import os

logger = logging.getLogger(__name__)

# Extensions that appear in the model picker.
_MODEL_EXTENSIONS = (".gltf", ".glb")
# Extensions the server may serve: models plus their external buffer/image sidecars
# (a text .gltf references a companion .bin buffer that the loader fetches separately).
_SERVABLE_EXTENSIONS = (".gltf", ".glb", ".bin", ".png", ".jpg", ".jpeg")
# A model's sidecars sit beside it as "<stem><suffix>".
_BOM_SUFFIX = ".bom.json"
_PLAN_SUFFIX = ".plan.svg"


class ModelCatalog:
    """Lists and safely resolves model files within a single directory."""

    def __init__(self, directory: str) -> None:
        """:param directory: Directory to scan for model files."""
        self._directory = os.path.abspath(directory)

    def model_names(self) -> list[str]:
        """Sorted base names of model files in the directory (empty if none/missing)."""
        if not os.path.isdir(self._directory):
            return []
        names = [
            entry
            for entry in os.listdir(self._directory)
            if entry.lower().endswith(_MODEL_EXTENSIONS)
            and os.path.isfile(os.path.join(self._directory, entry))
        ]
        return sorted(names)

    def resolve(self, name: str) -> str | None:
        """Resolve a model ``name`` to an absolute path, or None if unknown/unsafe.

        Rejects path traversal and any name not directly inside the directory.
        """
        candidate = os.path.abspath(os.path.join(self._directory, name))
        if os.path.dirname(candidate) != self._directory:
            return None
        if not candidate.lower().endswith(_SERVABLE_EXTENSIONS):
            return None
        if not os.path.isfile(candidate):
            return None
        return candidate

    def resolve_bom(self, model_name: str) -> str | None:
        """Resolve a model name to its BOM sidecar (``<stem>.bom.json``), or None."""
        return self._resolve_sidecar(model_name, _BOM_SUFFIX)

    def resolve_plan(self, model_name: str) -> str | None:
        """Resolve a model name to its plan sidecar (``<stem>.plan.svg``), or None."""
        return self._resolve_sidecar(model_name, _PLAN_SUFFIX)

    def _resolve_sidecar(self, model_name: str, suffix: str) -> str | None:
        """Resolve ``<stem><suffix>`` beside the model, or None if unsafe/absent."""
        stem = os.path.splitext(model_name)[0]
        candidate = os.path.abspath(os.path.join(self._directory, stem + suffix))
        if os.path.dirname(candidate) != self._directory:
            return None
        if not os.path.isfile(candidate):
            return None
        return candidate
