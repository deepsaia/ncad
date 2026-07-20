"""End-to-end coverage for bucket 1.6 conic + text sketch entities.

Builds each gate example on the real kernel (slow), round-trips to STEP, and checks
determinism + a golden geometry signature.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-1.6"
_GOLDEN = Path(__file__).resolve().parents[1] / "build" / "golden"


@pytest.mark.parametrize("name", ["nameplate", "guitar_pick"])
def test_gate_1_6_builds_and_step_round_trips(name, tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_DIR / f"{name}.hocon"), str(tmp_path), formats=("step",))["artifacts"]
    step_path = Path(artifacts[name])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.parametrize("name", ["nameplate", "guitar_pick"])
def test_gate_1_6_is_deterministic(name):
    from ncad.build.equality_comparator import EqualityComparator

    sig1, sig2 = _signature(name), _signature(name)
    comparator = EqualityComparator()
    assert comparator.equal(sig1, sig2), comparator.explain(sig1, sig2)


@pytest.mark.parametrize("name", ["nameplate", "guitar_pick"])
def test_gate_1_6_signature_matches_golden(name):
    from ncad.build.equality_comparator import EqualityComparator

    golden = json.loads((_GOLDEN / f"{name}.signature.json").read_text())
    live = _signature(name)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


def _signature(name: str) -> dict:
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(
        builder._loader.load(str(_DIR / f"{name}.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"][name])
    assert result.shape is not None
    return kernel.signature(result.shape)
