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

    def motions_with_labels(self) -> list[dict]:
        """Motion names each with a short DECLARED-value label for the picker (fps or steps).

        The label reports what the driver actually declared, never a derived number: ``30fps`` when
        the driver used ``fps`` (+ duration), else ``72 steps`` (the smoothness knob), else ``73f``
        as a last resort (frame count from the trajectory). Reading is best-effort: a
        missing/unreadable trajectory yields no label rather than failing the listing.
        """
        result: list[dict] = []
        for name in self.motion_names():
            result.append({"name": name, "label": self._motion_label(name)})
        return result

    def _motion_label(self, name: str) -> str | None:
        """The declared driver label for one motion, or None if the trajectory can't be read."""
        path = self.resolve_motion(name)
        if path is None:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            logger.warning("could not read motion label for %s: %s", name, exc)
            return None
        driver = doc.get("driver") or {}
        if driver.get("fps") is not None:
            return f"{_trim(driver['fps'])}fps"
        if driver.get("steps") is not None:
            return f"{int(driver['steps'])} steps"
        frames = doc.get("frames")
        return f"{len(frames)}f" if isinstance(frames, list) and frames else None

    def resolve_motion(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.motion.json`` (the trajectory), or None if absent.

        Rejects path traversal and any name not directly inside the directory (mirrors
        resolve_assembly). The viewer fetches this by the assembly stem to play back motion.
        """
        candidate = os.path.abspath(os.path.join(self._directory, name + ".motion.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def robot_names(self) -> list[str]:
        """Robot names that have a Physics-viewer tree (files ending in .robot.json)."""
        if not os.path.isdir(self._directory):
            return []
        suffix = ".robot.json"
        return sorted(entry[: -len(suffix)] for entry in os.listdir(self._directory)
                      if entry.lower().endswith(suffix)
                      and os.path.isfile(os.path.join(self._directory, entry)))

    def robots_with_labels(self) -> list[dict]:
        """Robot names each with a short label + recorded source for the picker.

        ``source`` is the ``.physics.hocon`` the robot was built from (recorded in the tree), so the
        viewer can Regenerate after a page reload, exactly as the assembly/motion lists do.
        """
        result: list[dict] = []
        for name in self.robot_names():
            result.append({"name": name, "label": self._robot_label(name),
                           "source": self._robot_source(name)})
        return result

    def _robot_source(self, name: str) -> str | None:
        """The ``source`` field recorded in a robot's ``.robot.json`` tree, or None."""
        path = self.resolve_robot(name)
        if path is None:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle).get("source")
        except (OSError, ValueError) as exc:
            logger.warning("could not read robot source for %s: %s", name, exc)
            return None

    def _robot_label(self, name: str) -> str | None:
        """A short label for one robot (its joint count), or None if the tree can't be read."""
        path = self.resolve_robot(name)
        if path is None:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            logger.warning("could not read robot label for %s: %s", name, exc)
            return None
        joints = doc.get("joints")
        return f"{len(joints)}j" if isinstance(joints, list) and joints else None

    def resolve_robot(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.robot.json`` (the tree), or None if absent."""
        candidate = os.path.abspath(os.path.join(self._directory, name + ".robot.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def resolve_robot_sweeps(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.robot_sweeps.json`` (joint sweeps), or None if absent."""
        candidate = os.path.abspath(os.path.join(self._directory, name + ".robot_sweeps.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def analysis_names(self) -> list[str]:
        """Analysis names that have an FEA result (files ending in .analysis.json).

        The ``.analysis.mesh.json`` field-mesh sidecar ends in ``.mesh.json`` so it is not counted
        as a separate analysis.
        """
        if not os.path.isdir(self._directory):
            return []
        suffix = ".analysis.json"
        return sorted(entry[: -len(suffix)] for entry in os.listdir(self._directory)
                      if entry.lower().endswith(suffix)
                      and os.path.isfile(os.path.join(self._directory, entry)))

    def analyses_with_labels(self) -> list[dict]:
        """Analysis names each with a label (peak von Mises) + recorded source, for the picker."""
        result: list[dict] = []
        for name in self.analysis_names():
            result.append({"name": name, "label": self._analysis_label(name),
                           "source": self._analysis_source(name)})
        return result

    def _analysis_source(self, name: str) -> str | None:
        """The ``source`` field recorded in an ``.analysis.json``, or None."""
        path = self.resolve_analysis(name)
        if path is None:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle).get("source")
        except (OSError, ValueError) as exc:
            logger.warning("could not read analysis source for %s: %s", name, exc)
            return None

    def _analysis_label(self, name: str) -> str | None:
        """A short label for one analysis (its max von Mises stress), or None if unreadable."""
        path = self.resolve_analysis(name)
        if path is None:
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                summary = json.load(handle).get("summary") or {}
        except (OSError, ValueError) as exc:
            logger.warning("could not read analysis label for %s: %s", name, exc)
            return None
        peak = summary.get("max_von_mises")
        return f"{peak:.3g} Pa" if isinstance(peak, (int, float)) and peak else None

    def resolve_analysis(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.analysis.json`` (the summary), or None if absent."""
        candidate = os.path.abspath(os.path.join(self._directory, name + ".analysis.json"))
        if os.path.dirname(candidate) != self._directory:
            return None
        return candidate if os.path.isfile(candidate) else None

    def resolve_analysis_mesh(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.analysis.mesh.json`` (field mesh), or None if absent."""
        candidate = os.path.abspath(os.path.join(self._directory, name + ".analysis.mesh.json"))
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
        # Remove the motion trajectory + the Physics-viewer robot sidecars keyed by the same name.
        for companion in (self.resolve_motion(name), self.resolve_robot(name),
                          self.resolve_robot_sweeps(name)):
            if companion is not None:
                os.remove(companion)
        return name

    def delete_robot(self, name: str) -> str | None:
        """Delete a robot's Physics-viewer sidecars (``.robot.json`` + ``.robot_sweeps.json``).

        Returns the name, or None if the robot is unknown. Only the two robot sidecars are removed:
        the composed assembly scene + the shared part glbs are ordinary build output left in place
        (the Assemblies view or another robot may use them), mirroring ``delete_assembly``.
        """
        resolved = self.resolve_robot(name)
        if resolved is None:
            return None
        os.remove(resolved)
        sweeps = self.resolve_robot_sweeps(name)
        if sweeps is not None:
            os.remove(sweeps)
        return name

    def delete_analysis(self, name: str) -> str | None:
        """Delete an analysis result's sidecars (``.analysis.json`` + ``.analysis.mesh.json``).

        Returns the name, or None if unknown. The meshed ``.inp`` / exported ``.step`` are ordinary
        build output left in place (cheap to regenerate), mirroring ``delete_robot``.
        """
        resolved = self.resolve_analysis(name)
        if resolved is None:
            return None
        os.remove(resolved)
        mesh = self.resolve_analysis_mesh(name)
        if mesh is not None:
            os.remove(mesh)
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


def _trim(value: float) -> str:
    """Format a number for a label, dropping a trailing ``.0`` (30.0 -> "30", 24.5 -> "24.5")."""
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)
