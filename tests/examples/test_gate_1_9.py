import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-1.9"
_GOLDEN = Path(__file__).resolve().parents[1] / "build" / "golden"


def _build():
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    result = DocumentBuilder(kernel).build_file_document(str(_DIR / "finial.hocon"))["finial"]
    return kernel, result


def test_gate_1_9_finial_builds_one_solid():
    kernel, result = _build()
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    # A single fused solid (base + twisted shaft + cap unioned into one body).
    assert len(kernel.bodies(result.shape)) == 1


def test_gate_1_9_signature_matches_golden():
    from ncad.build.equality_comparator import EqualityComparator

    kernel, result = _build()
    live = kernel.signature(result.shape)
    golden_path = _GOLDEN / "finial.signature.json"
    if not golden_path.exists():
        golden_path.write_text(json.dumps(live, indent=2, default=list))
    golden = json.loads(golden_path.read_text())
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
