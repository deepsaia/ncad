"""Discover 3D model files (glTF/GLB) in a directory for the browser viewer.

Keeps filesystem concerns out of the HTTP server: the server asks the catalog what
models exist and resolves a requested name to a safe absolute path (rejecting anything
outside the directory, so a crafted name can't escape via ``..``).
"""

import json
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
_META_SUFFIX = ".meta.json"
_ELEMENTMAP_SUFFIX = ".elementmap.json"
_HIERARCHY_SUFFIX = ".hierarchy.json"
_STATUS_SUFFIX = ".status.json"
# All sidecar suffixes removed alongside a model on delete.
_SIDECAR_SUFFIXES = (_META_SUFFIX, _BOM_SUFFIX, _PLAN_SUFFIX, _ELEMENTMAP_SUFFIX,
                     _HIERARCHY_SUFFIX, _STATUS_SUFFIX)


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

    def assembly_names(self) -> list[str]:
        """Assembly scene names (files ending in .assembly.json), without the suffix."""
        if not os.path.isdir(self._directory):
            return []
        suffix = ".assembly.json"
        return sorted(entry[: -len(suffix)] for entry in os.listdir(self._directory)
                      if entry.lower().endswith(suffix)
                      and os.path.isfile(os.path.join(self._directory, entry)))

    def resolve_assembly(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.assembly.json``, or None if unsafe/absent.

        Rejects path traversal and any name not directly inside the directory (mirrors resolve).
        """
        candidate = os.path.abspath(os.path.join(self._directory, name + ".assembly.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def motion_names(self) -> list[str]:
        """Assembly names that have a motion trajectory (files ending in .motion.json)."""
        if not os.path.isdir(self._directory):
            return []
        suffix = ".motion.json"
        return sorted(entry[: -len(suffix)] for entry in os.listdir(self._directory)
                      if entry.lower().endswith(suffix)
                      and os.path.isfile(os.path.join(self._directory, entry)))

    def resolve_motion(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.motion.json`` (the trajectory), or None if absent.

        Rejects path traversal and any name not directly inside the directory (mirrors
        resolve_assembly). The viewer fetches this by the assembly stem to play back motion.
        """
        candidate = os.path.abspath(os.path.join(self._directory, name + ".motion.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def delete_assembly(self, name: str) -> str | None:
        """Delete ``<name>.assembly.json`` (the composed scene). Returns the name, or None.

        The shared part glbs are ordinary build output and are left in place (other assemblies
        or the part view may use them); only the assembly scene sidecar (and its motion
        trajectory, if any) is removed.
        """
        resolved = self.resolve_assembly(name)
        if resolved is None:
            return None
        os.remove(resolved)
        motion = self.resolve_motion(name)
        if motion is not None:
            os.remove(motion)
        return name

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

    def resolve_meta(self, model_name: str) -> str | None:
        """Resolve a model name to its metadata sidecar (``<stem>.meta.json``), or None."""
        return self._resolve_sidecar(model_name, _META_SUFFIX)

    def resolve_elementmap(self, model_name: str) -> str | None:
        """Resolve a model name to its element-map sidecar, or None."""
        return self._resolve_sidecar(model_name, _ELEMENTMAP_SUFFIX)

    def resolve_hierarchy(self, model_name: str) -> str | None:
        """Resolve a model name to its hierarchy sidecar, or None."""
        return self._resolve_sidecar(model_name, _HIERARCHY_SUFFIX)

    def resolve_status(self, model_name: str) -> str | None:
        """Resolve a model name to its sketch-status sidecar, or None."""
        return self._resolve_sidecar(model_name, _STATUS_SUFFIX)

    def models_with_sources(self) -> list[dict]:
        """List models with their recorded source spec (from meta), source None if absent."""
        return [{"name": name, "source": self._read_source(name)} for name in self.model_names()]

    def delete_model(self, model_name: str) -> list[str] | None:
        """Delete the model file and its sidecars from this directory (path-safe).

        :return: Absolute paths removed, or None if the model is unknown or unsafe.
        """
        target = self.resolve(model_name)
        if target is None:
            return None
        removed = [target]
        os.remove(target)
        stem = os.path.splitext(model_name)[0]
        for suffix in _SIDECAR_SUFFIXES:
            sidecar = os.path.abspath(os.path.join(self._directory, stem + suffix))
            if os.path.dirname(sidecar) == self._directory and os.path.isfile(sidecar):
                os.remove(sidecar)
                removed.append(sidecar)
        logger.debug("deleted model %s and %d sidecar(s)", model_name, len(removed) - 1)
        return removed

    def _read_source(self, model_name: str) -> str | None:
        """Read the ``source`` field from a model's meta sidecar, or None."""
        meta_path = self.resolve_meta(model_name)
        if meta_path is None:
            return None
        try:
            with open(meta_path, encoding="utf-8") as handle:
                return json.load(handle).get("source")
        except (OSError, ValueError):
            logger.warning("could not read meta for %s", model_name)
            return None
