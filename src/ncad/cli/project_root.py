"""Locate the ncad project root so CLI commands work from any subdirectory.

The root is the nearest ancestor directory containing a ``pyproject.toml``. This lets
``nc`` resolve the default models directory relative to the project, not the caller's
current working directory.
"""

from pathlib import Path

_MARKER = "pyproject.toml"


def find_project_root(start: Path | None = None) -> Path:
    """Return the nearest ancestor of ``start`` that contains ``pyproject.toml``.

    :param start: Directory to search upward from; defaults to the current directory.
    :return: The project root directory.
    :raises FileNotFoundError: If no ``pyproject.toml`` is found in ``start`` or any
        of its parents.
    """
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / _MARKER).is_file():
            return directory
    raise FileNotFoundError(
        f"no {_MARKER} found in {current} or any parent; is this inside the ncad project?"
    )
