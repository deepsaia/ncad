"""End-to-end coverage for bucket 2.3.5 spline/curve sketch entities.

Builds each gate example on the real kernel (slow) and round-trips it to STEP.
"""

from pathlib import Path

import pytest

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-2.3.5"


@pytest.mark.slow
@pytest.mark.parametrize("name", ["spline_profile", "bezier_sweep"])
def test_spline_example_builds_and_step_round_trips(name, tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_DIR / f"{name}.hocon"), str(tmp_path), formats=("step",))
    step_path = Path(artifacts[name])
    assert step_path.is_file()
    # Validity is by measure magnitude (design section 4a), not orientation sign.
    assert abs(import_step(str(step_path)).volume) > 0
