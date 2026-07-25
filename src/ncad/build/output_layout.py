"""The single owner of the out/ directory layout: out/<kind>/<name>/ per build target.

Every writer asks this where to put artifacts; ModelCatalog asks it where to scan/resolve. Keeping
the tree shape (and the security-guarded resolution) in one place makes the layout changeable in one
edit and is the seam a future stateless ArtifactStore (object store keyed by <kind>/<name>/<file>)
slots behind. Motion is an assembly overlay, so it has no kind dir (its trajectory lives in the
assembly's dir). One class.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class OutputLayout:
    """Maps (kind, name) to out/<kind>/<name>/ and resolves files within it, path-traversal-safe."""

    KINDS = ("parts", "assemblies", "robots", "analyses")
    SERVABLE_EXTENSIONS = (".gltf", ".glb", ".bin", ".png", ".jpg", ".jpeg")

    def __init__(self, root: str) -> None:
        """:param root: the models output root (the historical flat ``out/``)."""
        self._root = os.path.abspath(root)

    def dir_for(self, kind: str, name: str) -> Path:
        """The directory ``out/<kind>/<name>/`` for a build target (creates nothing)."""
        return Path(self._root) / kind / name

    def names(self, kind: str) -> list[str]:
        """Sorted target names under ``out/<kind>/`` (empty if absent); dot-dirs are skipped."""
        kind_dir = Path(self._root) / kind
        if not kind_dir.is_dir():
            return []
        return sorted(entry.name for entry in kind_dir.iterdir()
                      if entry.is_dir() and not entry.name.startswith("."))

    def resolve(self, kind: str, name: str, filename: str) -> str | None:
        """A path-safe absolute path to ``out/<kind>/<name>/<filename>``, or None if unsafe/absent.

        Traversal guard: abspath (textual, no symlink following) + the resolved path must stay
        inside the target dir, so ``..``/absolute/sibling-escaping values return None.
        """
        target = os.path.abspath(str(self.dir_for(kind, name)))
        candidate = os.path.abspath(os.path.join(target, filename))
        if os.path.commonpath([candidate, target]) != target:
            return None
        return candidate if os.path.isfile(candidate) else None

    def servable(self, name: str) -> str | None:
        """Find a servable file ``name`` (glb/bin/png) under parts/ then assemblies/, or None.

        Backs the viewer's bare-name GET /models/<name> (and its glTF companion buffers/images).
        Bounded to the two kinds that emit meshes; first containment-safe existing match wins.
        """
        if not name.lower().endswith(self.SERVABLE_EXTENSIONS):
            return None
        for kind in ("parts", "assemblies"):
            for target_name in self.names(kind):
                resolved = self.resolve(kind, target_name, name)
                if resolved is not None:
                    return resolved
        return None
