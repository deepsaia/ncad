"""End-to-end STEP export coverage for bucket 2.0.

Builds a real part on the build123d kernel (slow) and asserts it exports a STEP file that
re-imports as a valid solid with a matching volume, per design section 4a (structural
round-trip, not a byte hash).
"""

from pathlib import Path

import pytest

_EXAMPLE = (Path(__file__).resolve().parents[2]
            / "examples" / "gate-2.0" / "step_block.hocon")


@pytest.mark.slow
def test_step_export_round_trips(tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_EXAMPLE), str(tmp_path), formats=("step",))

    step_path = Path(artifacts["step_block"])
    assert step_path.suffix == ".step" and step_path.is_file()
    reimported = import_step(str(step_path))
    # a 40 x 24 x 10 block = 9600 mm^3; the re-imported solid volume matches within epsilon
    assert reimported.volume == pytest.approx(40.0 * 24.0 * 10.0, rel=1e-6)


@pytest.mark.slow
def test_step_and_glb_both_written(tmp_path):
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    DocumentBuilder(Build123dKernel()).build_file(
        str(_EXAMPLE), str(tmp_path), formats=("glb", "step"))
    assert (tmp_path / "step_block.glb").is_file()
    assert (tmp_path / "step_block.step").is_file()
