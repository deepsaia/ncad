import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-1.7"
_GOLDEN = Path(__file__).resolve().parents[1] / "build" / "golden"


def _build():
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    result = DocumentBuilder(kernel).build_file_document(
        str(_DIR / "rocker_arm.hocon"))["rocker_arm"]
    return kernel, result


def test_gate_1_7_rocker_arm_builds_and_solves_well():
    _kernel, result = _build()
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    # The sketch is fully constrained (dof 0): no under-constrained warning survives.
    assert not [i for i in result.issues if "under-constrained" in i.message]


def test_gate_1_7_signature_matches_golden():
    from ncad.build.equality_comparator import EqualityComparator

    kernel, result = _build()
    live = kernel.signature(result.shape)
    golden_path = _GOLDEN / "rocker_arm.signature.json"
    if not golden_path.exists():
        golden_path.write_text(json.dumps(live, indent=2, default=list))
    golden = json.loads(golden_path.read_text())
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
