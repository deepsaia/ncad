"""Build a feature-tree document to glTF: ``python -m ncad.build <document> [--out DIR]``.

Thin entrypoint that delegates to :class:`ncad.cli.viewer_cli.ViewerCli` so the module
argument path and the ``ncad build`` console command share one implementation.
"""

import argparse
import logging

from ncad.cli.viewer_cli import ViewerCli

logger = logging.getLogger(__name__)


class BuildMain:
    """Parses ``python -m ncad.build`` arguments and builds the document."""

    def run(self) -> None:
        """Parse args, build the document, and print the written artifacts."""
        parser = argparse.ArgumentParser(description="ncad build a feature-tree document to glTF")
        parser.add_argument("document", help="path to a .hocon/.json feature-tree document")
        parser.add_argument("--out", default=None, help="output directory for .glb files")
        args = parser.parse_args()

        artifacts = ViewerCli().build_document(args.document, args.out)
        print(f"\nncad build: {args.document}")
        for name, path in artifacts.items():
            print(f"  part {name:12} {path}")
        if artifacts:
            out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
            print(f"\nview with:  ncad view {out_dir}\n")
        else:
            print("  no parts built\n")


def main() -> None:
    """Console-script / module entrypoint."""
    BuildMain().run()


if __name__ == "__main__":
    main()
