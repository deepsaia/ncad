"""End-to-end coverage for bucket 2.1 end-conditions.

Builds the gate example on the real kernel (slow) and round-trips it to STEP, proving the
symmetric/through-all/draft composition builds a valid solid that exports clean STEP.
"""

from pathlib import Path

import pytest

_EXAMPLE = (Path(__file__).resolve().parents[2]
            / "examples" / "gate-2.1" / "end_conditions.hocon")


@pytest.mark.slow
def test_end_conditions_build_and_step_round_trip(tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_EXAMPLE), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["end_conditions"])
    assert step_path.is_file()
    solid = import_step(str(step_path))
    assert solid.volume > 0
