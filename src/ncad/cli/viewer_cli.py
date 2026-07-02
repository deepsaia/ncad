"""The ``ncad`` command-line app (typer).

Runnable from any subdirectory of the project. Bare ``ncad`` and ``ncad view [dir]``
both launch the browser 3D viewer over a directory of glTF/GLB models; the directory
defaults to ``<project-root>/out`` and any relative path is resolved against the
project root, so the command behaves the same wherever it is run.
"""

import logging
from pathlib import Path

import typer

from ncad.cli.project_root import find_project_root
from ncad.viewer.viewer_server import ViewerServer

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="ncad: build and view parametric CAD models.",
    # Bare `ncad` runs the callback (which launches the viewer) instead of printing
    # help; `ncad view` is the explicit form, and future commands (e.g. `ncad build`)
    # slot in as siblings without changing this default.
    invoke_without_command=True,
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


def launch_viewer(models_dir: str | None, host: str, port: int) -> None:
    """Resolve the models directory and run the viewer server in the foreground."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    resolved = resolve_models_dir(models_dir)
    server = ViewerServer(models_dir=str(resolved), host=host, port=port)
    print(f"ncad viewer >> {server.base_url}  (serving '{resolved}', Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...")
        server.stop()


@app.callback()
def _root(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
) -> None:
    """ncad: build and view parametric CAD models. Bare ``ncad`` launches the viewer."""
    if ctx.invoked_subcommand is None:
        launch_viewer(None, host, port)


@app.command()
def view(
    models_dir: str = typer.Argument(None, help="directory of glTF/GLB models (default: out/)"),
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
) -> None:
    """Launch the browser 3D viewer over a directory of models."""
    launch_viewer(models_dir, host, port)


@app.command()
def build(
    document: str = typer.Argument(..., help="path to a .hocon/.json feature-tree document"),
    out: str = typer.Option(None, help="output directory for .glb files (default: out/)"),
) -> None:
    """Build every part in a feature-tree document to glTF."""
    # Imported here, not at module top, so `ncad`/`ncad view` never pay the OCP cost.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("build123d").setLevel(logging.WARNING)
    out_dir = resolve_models_dir(out)
    artifacts = DocumentBuilder(Build123dKernel()).build_file(document, str(out_dir))

    print(f"\nncad build: {document}")
    for name, path in artifacts.items():
        print(f"  part {name:12} {path}")
    if artifacts:
        print(f"\nview with:  ncad view {out_dir}\n")
    else:
        print("  no parts built\n")


def main() -> None:
    """Console-script entrypoint for ``ncad``."""
    app()


if __name__ == "__main__":
    main()
