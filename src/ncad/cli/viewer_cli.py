"""The ``ncad`` command-line app (typer).

Runnable from any subdirectory of the project. ``ncad view [dir]`` launches the
browser 3D viewer over a directory of glTF/GLB models; the directory defaults to
``<project-root>/out`` and any relative path is resolved against the project root, so
the command behaves the same wherever it is run.
"""

import logging
from pathlib import Path

import typer

from ncad.cli.project_root import find_project_root
from ncad.viewer.viewer_server import ViewerServer

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="ncad: build and view parametric CAD models.",
    no_args_is_help=True,
    # Keep `view` an explicit subcommand even while it is the only one, so future
    # commands (e.g. `ncad build`) slot in without changing the `ncad view` interface.
    add_completion=False,
)

_DEFAULT_MODELS_SUBDIR = "out"


def resolve_models_dir(models_dir: str | None, start: Path | None = None) -> Path:
    """Resolve the models directory against the project root.

    :param models_dir: The requested directory. ``None`` means ``<root>/out``. A
        relative path is resolved against the project root; an absolute path is used
        as given.
    :param start: Directory to locate the project root from (defaults to cwd).
    :return: The resolved models directory path.
    """
    root = find_project_root(start)
    if models_dir is None:
        return root / _DEFAULT_MODELS_SUBDIR
    candidate = Path(models_dir)
    return candidate if candidate.is_absolute() else root / candidate


@app.callback()
def _root() -> None:
    """ncad: build and view parametric CAD models."""


@app.command()
def view(
    models_dir: str = typer.Argument(None, help="directory of glTF/GLB models (default: out/)"),
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
) -> None:
    """Launch the browser 3D viewer over a directory of models."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    resolved = resolve_models_dir(models_dir)
    server = ViewerServer(models_dir=str(resolved), host=host, port=port)
    print(f"ncad viewer >> {server.base_url}  (serving '{resolved}', Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...")
        server.stop()


def main() -> None:
    """Console-script entrypoint for ``ncad``."""
    app()


if __name__ == "__main__":
    main()
