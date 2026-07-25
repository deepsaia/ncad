"""Discover built models (glTF/GLB) + their sidecars for the browser viewer.

Keeps filesystem concerns out of the HTTP server: the server asks the catalog what models exist and
resolves a requested name to a safe absolute path. The on-disk layout is out/<kind>/<name>/ (see
OutputLayout); this catalog is a thin, name-based facade over it, so the HTTP API stays bare-name
(GET /models/<name>, /bom/<name>, ...). All path-traversal safety lives in OutputLayout.resolve.
"""

import json
import logging
import shutil
from pathlib import Path

from ncad.build.output_layout import OutputLayout

logger = logging.getLogger(__name__)

# A model's sidecars sit beside it in its part dir as "<stem><suffix>".
_BOM_SUFFIX = ".bom.json"
_PLAN_SUFFIX = ".plan.svg"
_META_SUFFIX = ".meta.json"
_ELEMENTMAP_SUFFIX = ".elementmap.json"
_HIERARCHY_SUFFIX = ".hierarchy.json"
_STATUS_SUFFIX = ".status.json"
_MODEL_EXTENSIONS = (".gltf", ".glb")


class ModelCatalog:
    """Lists + safely resolves models/sidecars in the out/<kind>/<name>/ tree via OutputLayout."""

    def __init__(self, directory: str) -> None:
        """:param directory: the models output root (the historical flat ``out/``)."""
        self._layout = OutputLayout(directory)

    def model_names(self) -> list[str]:
        """Sorted glb/gltf filenames of built parts (the viewer fetches models by filename)."""
        names: list[str] = []
        for stem in self._layout.names("parts"):
            for ext in _MODEL_EXTENSIONS:
                if self._layout.resolve("parts", stem, f"{stem}{ext}") is not None:
                    names.append(f"{stem}{ext}")
                    break
        return sorted(names)

    def resolve(self, name: str) -> str | None:
        """Resolve a servable model/buffer/image by filename to a safe absolute path, or None.

        Searches the parts + assemblies dirs (the two kinds that emit meshes), so a member glb (and
        its glTF companion .bin/.png) resolves from its assembly dir. Path-traversal-safe.
        """
        return self._layout.servable(name)

    def assembly_names(self) -> list[str]:
        """Assembly scene names (dirs under out/assemblies/ with a <name>.assembly.json)."""
        return [n for n in self._layout.names("assemblies")
                if self._layout.resolve("assemblies", n, f"{n}.assembly.json") is not None]

    def resolve_assembly(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.assembly.json``, or None if unsafe/absent."""
        return self._layout.resolve("assemblies", name, f"{name}.assembly.json")

    def motion_names(self) -> list[str]:
        """Assembly names that have a motion trajectory (a <name>.motion.json in their dir)."""
        return [n for n in self._layout.names("assemblies")
                if self._layout.resolve("assemblies", n, f"{n}.motion.json") is not None]

    def motions_with_labels(self) -> list[dict]:
        """Motion names each with a short DECLARED-value label for the picker (fps or steps).

        The label reports what the driver actually declared, never a derived number: ``30fps`` when
        the driver used ``fps`` (+ duration), else ``72 steps`` (the smoothness knob), else ``73f``
        as a last resort (frame count from the trajectory). Best-effort: an unreadable trajectory
        yields no label rather than failing the listing.
        """
        return [{"name": name, "label": self._motion_label(name)} for name in self.motion_names()]

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
        """Safe absolute path to ``<name>.motion.json`` in the assembly dir, or None if absent."""
        return self._layout.resolve("assemblies", name, f"{name}.motion.json")

    def robot_names(self) -> list[str]:
        """Robot names that have a Physics-viewer tree (a <name>.robot.json in the robot dir)."""
        return [n for n in self._layout.names("robots")
                if self._layout.resolve("robots", n, f"{n}.robot.json") is not None]

    def robots_with_labels(self) -> list[dict]:
        """Robot names each with a short label + recorded source for the picker.

        ``source`` is the ``.physics.hocon`` the robot was built from (recorded in the tree), so the
        viewer can Regenerate after a page reload, exactly as the assembly/motion lists do.
        """
        return [{"name": name, "label": self._robot_label(name),
                 "source": self._robot_source(name)} for name in self.robot_names()]

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
        return self._layout.resolve("robots", name, f"{name}.robot.json")

    def resolve_robot_sweeps(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.robot_sweeps.json`` (joint sweeps), or None if absent."""
        return self._layout.resolve("robots", name, f"{name}.robot_sweeps.json")

    def analysis_names(self) -> list[str]:
        """Analysis names that have an FEA result (a <name>.analysis.json in the analysis dir)."""
        return [n for n in self._layout.names("analyses")
                if self._layout.resolve("analyses", n, f"{n}.analysis.json") is not None]

    def analyses_with_labels(self) -> list[dict]:
        """Analysis names each with a label (peak von Mises) + recorded source, for the picker."""
        return [{"name": name, "label": self._analysis_label(name),
                 "source": self._analysis_source(name)} for name in self.analysis_names()]

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
        return self._layout.resolve("analyses", name, f"{name}.analysis.json")

    def resolve_analysis_mesh(self, name: str) -> str | None:
        """Safe absolute path to ``<name>.analysis.mesh.json`` (field mesh), or None if absent."""
        return self._layout.resolve("analyses", name, f"{name}.analysis.mesh.json")

    def resolve_bom(self, model_name: str) -> str | None:
        """Resolve a model name to its BOM sidecar (``<stem>.bom.json``), or None."""
        return self._resolve_sidecar(model_name, _BOM_SUFFIX)

    def resolve_plan(self, model_name: str) -> str | None:
        """Resolve a model name to its plan sidecar (``<stem>.plan.svg``), or None."""
        return self._resolve_sidecar(model_name, _PLAN_SUFFIX)

    def _resolve_sidecar(self, model_name: str, suffix: str) -> str | None:
        """Resolve ``<stem><suffix>`` in the part's dir, or None if unsafe/absent."""
        stem = Path(model_name).stem
        return self._layout.resolve("parts", stem, f"{stem}{suffix}")

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
        """Delete a part's whole ``out/parts/<stem>/`` dir (glb + all sidecars).

        :return: ``[dir]`` removed, or None if the part is unknown.
        """
        return self._delete_dir("parts", Path(model_name).stem)

    def delete_assembly(self, name: str) -> str | None:
        """Delete an assembly's whole ``out/assemblies/<name>/`` dir (scene + members + motion)."""
        return name if self._delete_dir("assemblies", name) else None

    def delete_robot(self, name: str) -> str | None:
        """Delete a robot's ``out/robots/<name>/`` dir (tree + sweeps + keyframes + meshes)."""
        return name if self._delete_dir("robots", name) else None

    def delete_analysis(self, name: str) -> str | None:
        """Delete an analysis's whole ``out/analyses/<name>/`` dir (summary + field mesh + STEP)."""
        return name if self._delete_dir("analyses", name) else None

    def _delete_dir(self, kind: str, name: str) -> list[str] | None:
        """Remove the target's ``out/<kind>/<name>/`` dir; return ``[dir]`` or None if absent."""
        target = self._layout.dir_for(kind, name)
        if not target.is_dir():
            return None
        shutil.rmtree(target)
        logger.debug("deleted %s %s (%s)", kind, name, target)
        return [str(target)]

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
