"""Build the spike input corpus and export each solid to STEP under out/.

Primary corpus: the last-few actually-generated gate models (our real STEP output, which is
exactly what Phase 4 must be able to edit). A gate document may contain several parts, so every
part it builds enters the corpus. Supplementary: three synthetics engineered to hit the
documented OCCT cliffs (tangent-adjacent face, thin wall, sliver face), since a real part may
not happen to contain them. This is exploratory spike code: it calls the kernel + builder
directly and is not imported by src/.

build_corpus returns structured records ({name, path, input_class}) so the driver never has to
hardcode part names (gate docs expand to parts like pattern_studs/spoke_hub, split_block/...).
"""

import logging
import os
from pathlib import Path
from typing import Any

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Gate documents (primary corpus): hocon path -> input_class for every part it builds.
_GATE_DOCS = {
    "examples/gate-2.9/mounting_bracket.hocon": "real_filleted",
    "examples/gate-3.2/patterned_bodies.hocon": "real_multibody",
    "examples/gate-3.3/mirrored_bodies.hocon": "real_multibody",
    "examples/gate-3.4/multibody_algebra.hocon": "real_multibody",
    "examples/gate-3.5/materials_part.hocon": "real_multibody",
    "examples/gate-3.6/flanged_coupling.hocon": "real_multibody",
}


def _build_gate_steps(kernel: Build123dKernel, out_dir: str) -> list[dict[str, Any]]:
    """Rebuild every part of each gate document to STEP; return corpus records."""
    builder = DocumentBuilder(kernel)
    records: list[dict[str, Any]] = []
    for rel, input_class in _GATE_DOCS.items():
        hocon = str(_REPO_ROOT / rel)
        artifacts = builder.build_file(hocon, out_dir, formats=("step",))
        for name, step_path in artifacts.items():
            records.append({"name": name, "path": step_path, "input_class": input_class})
            logger.info("built gate STEP: %s -> %s", name, step_path)
    return records


def _build_synthetics(kernel: Build123dKernel, out_dir: str) -> list[dict[str, Any]]:
    """Build the three cliff synthetics directly and export STEP; return corpus records."""
    records: list[dict[str, Any]] = []

    # tangent_fillet_chain: a box with one edge filleted, so the fillet face is tangent to its
    # two neighbours (the documented defeature-on-tangent failure).
    box = kernel.extrude(kernel.polygon_face([(0, 0), (40, 0), (40, 20), (0, 20)], "XY"), 20.0)
    edges = kernel.edges_of(box)
    filleted = kernel.fillet_edges(box, [edges[0]["edge"]], 6.0)
    p1 = os.path.join(out_dir, "tangent_fillet_chain.step")
    kernel.export(filleted, p1)
    records.append({"name": "tangent_fillet_chain", "path": p1, "input_class": "synthetic_tangent"})

    # thin_wall_box: a shelled box with a thin remaining wall (the offset/thicken cliff).
    solid = kernel.extrude(kernel.polygon_face([(0, 0), (30, 0), (30, 30), (0, 30)], "XY"), 30.0)
    thin = kernel.shell(solid, 0.8)
    p2 = os.path.join(out_dir, "thin_wall_box.step")
    kernel.export(thin, p2)
    records.append({"name": "thin_wall_box", "path": p2, "input_class": "synthetic_thinwall"})

    # sliver_face_block: a block with one very narrow face (the small-face hang, #33561).
    sliver = kernel.extrude(
        kernel.polygon_face([(0, 0), (40, 0), (40, 0.4), (0, 0.4)], "XY"), 20.0
    )
    p3 = os.path.join(out_dir, "sliver_face_block.step")
    kernel.export(sliver, p3)
    records.append({"name": "sliver_face_block", "path": p3, "input_class": "synthetic_sliver"})

    for record in records:
        logger.info("built synthetic STEP: %s", record["path"])
    return records


def build_corpus(out_dir: str = "out") -> list[dict[str, Any]]:
    """Build the full input corpus, returning {name, path, input_class} records."""
    os.makedirs(out_dir, exist_ok=True)
    kernel = Build123dKernel()
    records = _build_gate_steps(kernel, out_dir)
    records.extend(_build_synthetics(kernel, out_dir))
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for entry in build_corpus():
        print(f"{entry['input_class']:20} {entry['name']:22} {entry['path']}")
