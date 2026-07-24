"""Discover feature-tree documents ("specs") under the examples directory for the viewer.

Returns the examples as a nested tree (directories before files, each group sorted by
name) so the viewer can render the same structure the filesystem has, and resolves a
requested relative spec path to a safe absolute path (rejecting traversal outside the
examples directory).
"""

import logging
import os

logger = logging.getLogger(__name__)

_SPEC_EXTENSIONS = (".hocon", ".conf", ".json")
# Document kind is detected by filename suffix, and the build path is chosen by kind: a part spec
# builds via `ncad build`, an assembly (.asm.hocon) via `ncad assemble`, and a motion study
# (.motion.hocon) via the motion path (it references an assembly + a driver, and solves a
# trajectory). Each appears in the spec tree tagged with `kind` so the viewer filters the combobox
# by its Parts / Assemblies / Motion mode.
_ASSEMBLY_EXTENSION = ".asm.hocon"
_MOTION_EXTENSION = ".motion.hocon"
_PHYSICS_EXTENSION = ".physics.hocon"
_ANALYSIS_EXTENSION = ".analysis.hocon"


def _is_spec(name: str) -> bool:
    """True if ``name`` is a spec document (part, assembly, or motion)."""
    return name.lower().endswith(_SPEC_EXTENSIONS)


def _spec_kind(name: str) -> str:
    """The spec kind by suffix: physics/analysis/motion/assembly, else part.

    ``.physics.hocon`` (robotics overlay), ``.analysis.hocon`` (FEA load case), and
    ``.motion.hocon`` all also end in ``.hocon``; the specific compound suffixes are tested first so
    they win over the bare part fallthrough.
    """
    lowered = name.lower()
    if lowered.endswith(_PHYSICS_EXTENSION):
        return "physics"
    if lowered.endswith(_ANALYSIS_EXTENSION):
        return "analysis"
    if lowered.endswith(_MOTION_EXTENSION):
        return "motion"
    if lowered.endswith(_ASSEMBLY_EXTENSION):
        return "assembly"
    return "part"


class SpecCatalog:
    """Lists and safely resolves spec documents within an examples directory."""

    def __init__(self, examples_dir: str) -> None:
        """:param examples_dir: Directory of example spec documents to scan. An empty
        string means "no examples directory" (the tree is empty, nothing is resolved),
        never the current working directory.
        """
        self._root = os.path.abspath(examples_dir) if examples_dir else ""

    def tree(self) -> list[dict]:
        """Nested tree of the examples directory; empty if unset or nonexistent."""
        if not self._root or not os.path.isdir(self._root):
            return []
        return self._scan(self._root)

    def resolve(self, rel_path: str) -> str | None:
        """Resolve a relative spec path to an absolute path under the examples dir.

        :return: The absolute path, or None if unsafe, absent, or not a spec file.
        """
        if not self._root:
            return None
        candidate = os.path.abspath(os.path.join(self._root, rel_path))
        if os.path.commonpath([candidate, self._root]) != self._root:
            return None
        if not _is_spec(candidate):
            return None
        if not os.path.isfile(candidate):
            return None
        return candidate

    def _scan(self, directory: str) -> list[dict]:
        """Return the sorted (dirs first) tree nodes for one directory."""
        dirs: list[dict] = []
        specs: list[dict] = []
        for entry in sorted(os.listdir(directory)):
            full = os.path.join(directory, entry)
            if os.path.isdir(full):
                dirs.append({"type": "dir", "name": entry, "children": self._scan(full)})
            elif _is_spec(entry):
                rel = os.path.relpath(full, self._root).replace(os.sep, "/")
                specs.append({"type": "spec", "name": entry, "path": rel,
                              "kind": _spec_kind(entry)})
        return dirs + specs
