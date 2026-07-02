"""Build a feature-tree document to glTF:

    python -m ncad.build tests/fixtures/parts/block.hocon --out out

Loads the document, validates it, builds every part, and writes ``<part>.glb`` into the
output directory. View the result with ``nc <out-dir>`` (or ``nv <out-dir>``).
"""

import argparse
import logging

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse args and build a document with the build123d kernel."""
    parser = argparse.ArgumentParser(description="ncad build a feature-tree document to glTF")
    parser.add_argument("document", help="path to a .hocon/.json feature-tree document")
    parser.add_argument("--out", default="out", help="output directory for .glb files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("build123d").setLevel(logging.WARNING)

    artifacts = DocumentBuilder(Build123dKernel()).build_file(args.document, args.out)

    print(f"\nncad build: {args.document}")
    for name, path in artifacts.items():
        print(f"  part {name:12} {path}")
    if artifacts:
        out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
        print(f"\nview with:  nc {out_dir}\n")
    else:
        print("  no parts built\n")


if __name__ == "__main__":
    main()
