"""Locate the ncad project root so CLI commands work from any subdirectory.

The root is the nearest ancestor directory containing a ``pyproject.toml``. This lets
the CLI resolve default directories (models, examples) relative to the project, not the
caller's current working directory.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ProjectRoot:
    """Finds the ncad project root (nearest ancestor with a ``pyproject.toml``)."""

    MARKER = "pyproject.toml"

    @classmethod
    def find(cls, start: Path | None = None) -> Path:
        """Return the nearest ancestor of ``start`` that contains ``pyproject.toml``.

        :param start: Directory to search upward from; defaults to the current directory.
        :return: The project root directory.
        :raises FileNotFoundError: If no ``pyproject.toml`` is found in ``start`` or any
            of its parents.
        """
        current = (start or Path.cwd()).resolve()
        for directory in (current, *current.parents):
            if (directory / cls.MARKER).is_file():
                return directory
        raise FileNotFoundError(
            f"no {cls.MARKER} found in {current} or any parent; "
            "is this inside the ncad project?"
        )
