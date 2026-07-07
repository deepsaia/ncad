"""End-to-end coverage for bucket 2.3 sweep/helix.

Builds each gate example on the real kernel (slow) and round-trips it to STEP.
"""

from pathlib import Path

import pytest

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-2.3"


@pytest.mark.slow
@pytest.mark.parametrize("name", ["swept_pipe", "coil_spring", "hvac_duct"])
def test_sweep_example_builds_and_step_round_trips(name, tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_DIR / f"{name}.hocon"), str(tmp_path), formats=("step",))
    step_path = Path(artifacts[name])
    assert step_path.is_file()
    # A swept solid can carry an inverted (negative) orientation from OCCT; validity is by
    # measure magnitude (design section 4a), not sign, so assert a non-zero volume.
    assert abs(import_step(str(step_path)).volume) > 0
