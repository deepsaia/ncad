"""The ``ncad`` command-line app (typer).

Runnable from any subdirectory of the project. Bare ``ncad`` and ``ncad view [dir]``
both launch the browser 3D viewer; ``ncad build <document>`` builds a feature-tree
document to glTF. Directories default to ``<project-root>/out`` (models) and
``<project-root>/examples`` (specs), and relative paths resolve against the project
root, so the command behaves the same wherever it is run.

All behavior lives on :class:`ViewerCli`; the typer commands are thin glue that
delegate to it.
"""

import logging
from pathlib import Path

import typer

from ncad.cli.project_root import ProjectRoot
from ncad.viewer.viewer_server import ViewerServer

logger = logging.getLogger(__name__)

_DEFAULT_MODELS_SUBDIR = "out"
_EXAMPLES_SUBDIR = "examples"


class ViewerCli:
    """Resolves project paths and runs the viewer / build actions for the CLI."""

    def resolve_models_dir(self, models_dir: str | None, start: Path | None = None) -> Path:
        """Resolve the models directory against the project root.

        :param models_dir: Requested directory. ``None`` means ``<root>/out``. A relative
            path resolves against the project root; an absolute path is used as given.
        :param start: Directory to locate the project root from (defaults to cwd).
        """
        root = ProjectRoot.find(start)
        if models_dir is None:
            return root / _DEFAULT_MODELS_SUBDIR
        candidate = Path(models_dir)
        return candidate if candidate.is_absolute() else root / candidate

    def resolve_examples_dir(self, start: Path | None = None) -> Path | None:
        """Return ``<project-root>/examples`` if it exists, else None."""
        root = ProjectRoot.find(start)
        candidate = root / _EXAMPLES_SUBDIR
        return candidate if candidate.is_dir() else None

    def launch_viewer(
        self, models_dir: str | None, host: str, port: int, dev: bool = False
    ) -> None:
        """Resolve the models and examples directories and run the viewer server."""
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        resolved = self.resolve_models_dir(models_dir)
        examples = self.resolve_examples_dir()
        server = ViewerServer(
            models_dir=str(resolved),
            host=host,
            port=port,
            examples_dir=str(examples) if examples else None,
            dev=dev,
        )
        print(f"ncad viewer >> {server.base_url}  (serving '{resolved}', Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nstopping...")
            server.stop()

    def launch_service(
        self, models_dir: str | None, host: str, port: int, dev: bool = False
    ) -> None:
        """Run the Tornado HTTP service (versioned JSON API + viewer SPA + Swagger UI).

        Same directory resolution as ``launch_viewer``; the service mounts the viewer at
        ``/viewer`` (``/`` redirects there), the JSON API under ``/api/v1``, and Swagger UI at
        ``/docs``. ``dev`` turns on server-side autoreload + browser live-reload.
        """
        from ncad.service.ncad_service import NcadService
        from ncad.service.service_logging import ServiceLogging

        # The service is long-running, so give the terminal colored, aligned log lines stamped with
        # the date + time to a tenth of a second (rich RichHandler; ships with typer). This also
        # colors Tornado's per-request access log (routed through the "tornado.access" logger),
        # unlike the one-shot build/view commands that just log bare messages.
        ServiceLogging().install()
        resolved = self.resolve_models_dir(models_dir)
        examples = self.resolve_examples_dir()
        service = NcadService(
            models_dir=str(resolved),
            host=host,
            port=port,
            examples_dir=str(examples) if examples else None,
            dev=dev,
        )
        print(f"ncad service >> {service.base_url}/viewer  (API {service.base_url}/api/v1, "
              f"docs {service.base_url}/docs; serving '{resolved}', Ctrl+C to stop)")
        try:
            service.serve_forever()
        except KeyboardInterrupt:
            print("\nstopping...")
            service.stop()

    def build_document(self, document: str, out: str | None,
                       formats: tuple[str, ...] = ("glb",)) -> dict[str, str]:
        """Build a feature-tree document; return the built artifacts by part.

        Imports the kernel lazily so the viewer commands never pay the OCP cost.
        ``formats`` selects the export format(s) (``glb`` and/or ``step``).
        """
        from ncad.build.document_builder import DocumentBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.getLogger("build123d").setLevel(logging.WARNING)
        out_dir = self.resolve_models_dir(out)
        result = DocumentBuilder(Build123dKernel()).build_file(
            document, str(out_dir), formats=formats)
        for diag in result["diagnostics"]:
            if diag.severity == "error":
                logging.error("%s [%s] %s", diag.code, diag.location, diag.message)
        return result["artifacts"]

    def import_document(self, file: str, out: str | None) -> dict[str, str]:
        """Build a one-feature import document from ``file``; return built artifacts.

        DocumentBuilder builds from a file path (no in-memory entry), so the one-feature
        import document is written to a temp JSON and built through the real build path.
        """
        import json
        import os
        import tempfile

        from ncad.build.document_builder import DocumentBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.getLogger("build123d").setLevel(logging.WARNING)
        out_dir = self.resolve_models_dir(out)
        document = {
            "units": "mm",
            "parts": {"imported": {"profile": "solid", "features": [
                {"id": "import", "op": "import", "file": os.path.abspath(file)}]}},
        }
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        try:
            json.dump(document, handle)
            handle.close()
            result = DocumentBuilder(Build123dKernel()).build_file(handle.name, str(out_dir))
            for diag in result["diagnostics"]:
                if diag.severity == "error":
                    logging.error("%s [%s] %s", diag.code, diag.location, diag.message)
            return result["artifacts"]
        finally:
            os.unlink(handle.name)

    def assemble_document(self, file: str, out: str | None) -> dict:
        """Compose an assembly document into the models directory; return the assemble result."""
        from ncad.assembly.assembly_builder import AssemblyBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.getLogger("build123d").setLevel(logging.WARNING)
        out_dir = self.resolve_models_dir(out)
        return AssemblyBuilder(Build123dKernel()).assemble(file, str(out_dir))

    def motion_document(self, file: str, out: str | None) -> dict:
        """Build a motion study document (drive its assembly + write a trajectory)."""
        from ncad.assembly.motion_builder import MotionBuilder
        from ncad.kernel.build123d_kernel import Build123dKernel

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.getLogger("build123d").setLevel(logging.WARNING)
        out_dir = self.resolve_models_dir(out)
        return MotionBuilder(Build123dKernel()).build(file, str(out_dir))

    def validate_document(self, file: str) -> dict:
        """Statically validate a part/assembly/motion document; return the ValidationReport dict.

        No kernel and no geometry: the loader reads the doc, DocumentValidator kind-dispatches and
        runs schema + semantic + cross-document reference checks, resolving referenced part/assembly
        files relative to the document's own directory. Never raises for a bad design.
        """
        import os

        from ncad.diagnostics.document_validator import DocumentValidator
        from ncad.spec.spec_loader import SpecLoader

        document = SpecLoader().load(file)
        report = DocumentValidator(base_dir=os.path.dirname(os.path.abspath(file))).validate(
            document)
        return report.to_dict()


app = typer.Typer(
    help="ncad: build and view parametric CAD models.",
    invoke_without_command=True,
    add_completion=False,
)
cli = ViewerCli()


@app.callback()
def _root(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
    dev: bool = typer.Option(True, help="hot-reload the viewer HTML on each request"),
) -> None:
    """ncad: build and view parametric CAD models. Bare ``ncad`` launches the viewer."""
    if ctx.invoked_subcommand is None:
        cli.launch_viewer(None, host, port, dev)


@app.command()
def view(
    models_dir: str = typer.Argument(None, help="directory of glTF/GLB models (default: out/)"),
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
    dev: bool = typer.Option(True, help="hot-reload the viewer HTML on each request"),
) -> None:
    """Launch the browser 3D viewer over a directory of models."""
    cli.launch_viewer(models_dir, host, port, dev)


@app.command()
def serve(
    models_dir: str = typer.Argument(None, help="directory of glTF/GLB models (default: out/)"),
    host: str = typer.Option("127.0.0.1", help="bind address"),
    port: int = typer.Option(8000, help="bind port (0 = ephemeral)"),
    dev: bool = typer.Option(True, help="hot-reload (server autoreload + browser live-reload)"),
) -> None:
    """Run the Tornado HTTP service: JSON API under /api/v1, viewer at /viewer, docs at /docs."""
    cli.launch_service(models_dir, host, port, dev)


@app.command()
def build(
    document: str = typer.Argument(..., help="path to a .hocon/.json feature-tree document"),
    out: str = typer.Option(None, help="output directory for artifacts (default: out/)"),
    format: str = typer.Option(
        "glb", "--format", "-f",
        help="comma-separated export formats: glb, step (default: glb)",
    ),
) -> None:
    """Build every part in a feature-tree document to the chosen format(s)."""
    # Reuse the ncad-build comma-list parser + validation so both entrypoints behave identically.
    from ncad.build.__main__ import _parse_formats

    formats = _parse_formats(format)
    artifacts = cli.build_document(document, out, formats=formats)
    print(f"\nncad build: {document}  [{', '.join(formats)}]")
    for name, path in artifacts.items():
        print(f"  part {name:12} {path}")
    if artifacts:
        out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
        print(f"\nview with:  ncad view {out_dir}\n")
    else:
        print("  no parts built\n")


@app.command("import")
def import_(
    file: str = typer.Argument(..., help="path to a STEP/IGES file to import as a base feature"),
    out: str = typer.Option(None, help="output directory (default: out/)"),
) -> None:
    """Import a dumb solid as an editable base-feature document."""
    artifacts = cli.import_document(file, out)
    print(f"\nncad import: {file}")
    for name, path in artifacts.items():
        print(f"  part {name:12} {path}")
    if artifacts:
        out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
        print(f"\nview with:  ncad view {out_dir}\n")
    else:
        print("  no parts built\n")


@app.command()
def assemble(
    document: str = typer.Argument(..., help="path to a .asm.hocon assembly document"),
    out: str = typer.Option(None, help="output directory (default: out/)"),
) -> None:
    """Compose an assembly (instances of parts, placed) into a viewable scene."""
    result = cli.assemble_document(document, out)
    print(f"\nncad assemble: {document}")
    for instance_id in result["instances"]:
        print(f"  instance {instance_id}")
    for issue in result["issues"]:
        print(f"  ISSUE [{issue['instance_id']}] {issue['message']}")
    out_dir = result["sidecar"].rsplit("/", 1)[0]
    print(f"\nview with:  ncad view {out_dir}\n")


@app.command()
def motion(
    document: str = typer.Argument(..., help="path to a .motion.hocon motion-study document"),
    out: str = typer.Option(None, help="output directory (default: out/)"),
) -> None:
    """Drive a mechanism: run a motion study (an assembly + a driver) into a trajectory."""
    result = cli.motion_document(document, out)
    print(f"\nncad motion: {document}")
    for issue in result["issues"]:
        print(f"  ISSUE {issue.get('instance_id', '')} {issue['message']}")
    if result.get("motion"):
        print(f"  trajectory: {result['motion']}")
    out_dir = result["sidecar"].rsplit("/", 1)[0]
    print(f"\nview with:  ncad view {out_dir}\n")


@app.command()
def validate(
    document: str = typer.Argument(..., help="path to a part/assembly/motion .hocon/.json doc"),
) -> None:
    """Statically validate a document (no geometry). Prints diagnostics; exits 1 if not ok."""
    report = cli.validate_document(document)
    diagnostics = report["diagnostics"]
    print(f"\nncad validate: {document}")
    for diag in diagnostics:
        marker = {"error": "ERROR", "warning": "WARN", "info": "INFO"}.get(diag["severity"], "?")
        print(f"  {marker} [{diag['stage']}/{diag['code']}] {diag['location']}: {diag['message']}")
        if diag.get("hint"):
            print(f"        hint: {diag['hint']}")
    if report["ok"]:
        print(f"\n  ok ({len(diagnostics)} diagnostic(s), no errors)\n")
    else:
        errors = sum(1 for d in diagnostics if d["severity"] == "error")
        print(f"\n  NOT ok: {errors} error(s)\n")
        raise typer.Exit(code=1)


def main() -> None:
    """Console-script entrypoint for ``ncad``."""
    app()


if __name__ == "__main__":
    main()
