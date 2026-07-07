"""End-to-end coverage for bucket 2.2 revolve/groove.

Builds the gate example on the real kernel (slow) and round-trips it to STEP.
"""

from pathlib import Path

import pytest

_EXAMPLE = (Path(__file__).resolve().parents[2]
            / "examples" / "gate-2.2" / "revolved_washer.hocon")


@pytest.mark.slow
def test_revolved_washer_builds_and_step_round_trips(tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_EXAMPLE), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["revolved_washer"])
    assert step_path.is_file()
    solid = import_step(str(step_path))
    assert solid.volume > 0
