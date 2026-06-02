"""Run the full ncad spine from the CLI:

    python -m ncad.pipeline --seed 42 --rooms 4 --width 12 --depth 9

Generates a building, validates it, builds the 3D model, and writes all artifacts
(model .glb, BOM .json, plan .svg, spec .json) into the output directory. Prints a
summary including any semantic issues. View the result with ``nv <out-dir>``.
"""

import argparse
import logging

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.pipeline.pipeline import Pipeline

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse args and run the pipeline with the build123d kernel."""
    parser = argparse.ArgumentParser(description="ncad — generate a building end to end")
    parser.add_argument("--seed", type=int, default=42, help="generation seed")
    parser.add_argument("--rooms", type=int, default=4, help="target number of rooms")
    parser.add_argument("--width", type=float, default=12.0, help="footprint width (m)")
    parser.add_argument("--depth", type=float, default=9.0, help="footprint depth (m)")
    parser.add_argument("--height", type=float, default=3.0, help="storey height (m)")
    parser.add_argument("--out", default="out", help="output directory")
    parser.add_argument("--name", default=None, help="base name for output files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # build123d logs builder-context info per solid; quiet it so our summary stays clean.
    logging.getLogger("build123d").setLevel(logging.WARNING)
    params = {
        "width": args.width,
        "depth": args.depth,
        "num_rooms": args.rooms,
        "storey_height": args.height,
    }
    result = Pipeline(Build123dKernel()).run(
        seed=args.seed, params=params, out_dir=args.out, name=args.name
    )

    _print_summary(result)


def _print_summary(result) -> None:
    """Print a human-readable summary of a pipeline result."""
    print(f"\nncad build — {result.name} (seed {result.seed})")
    print("  artifacts:")
    for kind, path in result.artifacts.items():
        print(f"    {kind:6} {path}")
    print("  bill of materials:")
    for key, value in result.bom.items():
        rendered = f"{value:.2f}" if isinstance(value, float) else value
        print(f"    {key:16} {rendered}")
    if result.semantic_issues:
        print(f"  semantic issues ({len(result.semantic_issues)}):")
        for issue in result.semantic_issues:
            print(f"    [{issue.kind}] {issue.entity_id}: {issue.message}")
    else:
        print("  semantic issues: none ✓")
    print(f"\nview with:  nv {result.artifacts['model'].rsplit('/', 1)[0]}\n")


if __name__ == "__main__":
    main()
