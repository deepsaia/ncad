"""Every gate example must build cleanly, so each gate stays a living artifact.

Fast pass builds all examples through the dependency-free FakeKernel and asserts no
build issues. A single slow pass builds the gate-0.1 example on the real build123d
kernel and checks the exported glb, proving the spine end to end.
"""

from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
_EXAMPLE_DOCS = sorted(_EXAMPLES_DIR.glob("gate-*/*.hocon"))


def test_examples_exist() -> None:
    assert _EXAMPLE_DOCS, "no gate example documents found under examples/gate-*/"


@pytest.mark.parametrize("doc_path", _EXAMPLE_DOCS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_example_builds_without_issues(doc_path: Path) -> None:
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc_path))

    assert results, f"{doc_path} produced no parts"
    for name, result in results.items():
        assert result.issues == [], f"{doc_path} part {name} had issues: {result.issues}"
        assert result.shape is not None


@pytest.mark.slow
def test_gate_0_1_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-0.1-first-shape" / "block.hocon"

    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["block"])
    assert glb.is_file() and glb.stat().st_size > 0
