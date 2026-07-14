"""End-to-end coverage for bucket 2.10 (Phase 2 completeness) gate parts.

Real, recognizable parts exercising datums, variable/face fillet, rib, draft, threads
(cosmetic + modeled), and curved-surface wrap. Each builds on the real kernel (slow),
round-trips to STEP, and matches a golden geometry signature.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-2.10"
_GOLDEN = Path(__file__).resolve().parents[1] / "build" / "golden"
_PARTS = ["hex_bolt", "threaded_stud", "control_knob", "shelf_bracket"]


@pytest.mark.parametrize("name", _PARTS)
def test_gate_2_10_builds_and_step_round_trips(name, tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_DIR / f"{name}.hocon"), str(tmp_path), formats=("step",))
    step_path = Path(artifacts[name])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.parametrize("name", _PARTS)
def test_gate_2_10_is_deterministic(name):
    from ncad.build.equality_comparator import EqualityComparator

    sig1, sig2 = _signature(name), _signature(name)
    comparator = EqualityComparator()
    assert comparator.equal(sig1, sig2), comparator.explain(sig1, sig2)


@pytest.mark.parametrize("name", _PARTS)
def test_gate_2_10_signature_matches_golden(name):
    from ncad.build.equality_comparator import EqualityComparator

    golden = json.loads((_GOLDEN / f"{name}.signature.json").read_text())
    live = _signature(name)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


def test_cosmetic_thread_records_a_callout_and_keeps_geometry():
    # The cosmetic thread (the default) records an M10 callout on provenance and passes the
    # running solid through unchanged (no geometry cut).
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.thread_op import ThreadOp

    stud = Solid.make_cylinder(5, 20)
    result = ThreadOp().build(stud, {"id": "t", "size": "M10"}, {}, Build123dKernel())
    assert result.shape is stud   # cosmetic: geometry unchanged
    assert any("M10" in v for v in result.provenance.values())


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
