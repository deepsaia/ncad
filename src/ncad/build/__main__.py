"""Build a feature-tree document to glTF: ``python -m ncad.build <document> [--out DIR]``.

Thin entrypoint that delegates to :class:`ncad.cli.viewer_cli.ViewerCli` so the module
argument path and the ``ncad build`` console command share one implementation.
"""

import argparse
import logging

from ncad.cli.viewer_cli import ViewerCli

logger = logging.getLogger(__name__)


def _parse_formats(raw: str) -> tuple[str, ...]:
    """Parse a comma-separated ``--format`` string into a validated tuple."""
    from ncad.build.document_builder import resolve_formats

    parts = tuple(p.strip().lower() for p in raw.split(",") if p.strip())
    return resolve_formats(parts or ("glb",))


class BuildMain:
    """Parses ``python -m ncad.build`` arguments and builds the document."""

    def run(self) -> None:
        """Parse args, build the document, and print the written artifacts."""
        parser = argparse.ArgumentParser(description="ncad build a feature-tree document")
        parser.add_argument("document", help="path to a .hocon/.json feature-tree document")
        parser.add_argument("--out", default=None, help="output directory for artifacts")
        parser.add_argument("--format", default="glb",
                            help="comma-separated export formats: glb, step (default: glb)")
        args = parser.parse_args()

        formats = _parse_formats(args.format)
        artifacts = ViewerCli().build_document(args.document, args.out, formats)
        print(f"\nncad build: {args.document}")
        for name, path in artifacts.items():
            print(f"  part {name:12} {path}")
        if artifacts:
            print(f"\n  formats: {', '.join(formats)}")
            out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
            print(f"\nview with:  ncad view {out_dir}\n")
        else:
            print("  no parts built\n")


def main() -> None:
    """Console-script / module entrypoint."""
    BuildMain().run()


if __name__ == "__main__":
    main()
