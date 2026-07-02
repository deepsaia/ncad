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


class SpecCatalog:
    """Lists and safely resolves spec documents within an examples directory."""

    def __init__(self, examples_dir: str) -> None:
        """:param examples_dir: Directory of example spec documents to scan."""
        self._root = os.path.abspath(examples_dir)

    def tree(self) -> list[dict]:
        """Nested tree of the examples directory; empty if it does not exist."""
        if not os.path.isdir(self._root):
            return []
        return self._scan(self._root)

    def resolve(self, rel_path: str) -> str | None:
        """Resolve a relative spec path to an absolute path under the examples dir.

        :return: The absolute path, or None if unsafe, absent, or not a spec file.
        """
        candidate = os.path.abspath(os.path.join(self._root, rel_path))
        if os.path.commonpath([candidate, self._root]) != self._root:
            return None
        if not candidate.lower().endswith(_SPEC_EXTENSIONS):
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
            elif entry.lower().endswith(_SPEC_EXTENSIONS):
                rel = os.path.relpath(full, self._root).replace(os.sep, "/")
                specs.append({"type": "spec", "name": entry, "path": rel})
        return dirs + specs
