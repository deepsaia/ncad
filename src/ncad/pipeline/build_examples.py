"""Compile every example brief in a directory into built artifacts.

Each ``examples/*.hocon`` is an agent-authorable brief; this compiles it to a spec via
``SpecCompiler`` and writes the model + BOM + plan into the output directory (default
``out/``) so the browser viewer (``nv``) can serve them. Run it after cloning to populate
``out/`` (which is gitignored — the briefs are the committed source of truth)::

    python -m ncad.pipeline.build_examples        # examples/ -> out/
    python -m ncad.pipeline.build_examples docs/  # custom brief dir
"""

import argparse
import glob
import logging
import os

from ncad.build.artifact_exporter import ArtifactExporter
from ncad.compile.spec_compiler import SpecCompiler
from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


def main() -> None:
    """Build every brief in the examples directory into the output directory."""
    parser = argparse.ArgumentParser(description="build ncad example briefs into models")
    parser.add_argument("examples_dir", nargs="?", default="examples", help="brief directory")
    parser.add_argument("--out", default="out", help="output directory for built models")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("build123d").setLevel(logging.WARNING)

    compiler = SpecCompiler()
    exporter = ArtifactExporter(Build123dKernel())
    briefs = sorted(glob.glob(os.path.join(args.examples_dir, "*.hocon")))
    for path in briefs:
        name = os.path.splitext(os.path.basename(path))[0]
        spec = compiler.compile(SpecLoader().load(path))
        exporter.export(spec, args.out, name)
        print(f"built {name}")
    print(f"\n{len(briefs)} model(s) in '{args.out}'.  View with:  nv {args.out}")


if __name__ == "__main__":
    main()
