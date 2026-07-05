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
# Examples that do not build a single closed face on the dependency-free FakeKernel are
# excluded from this sweep and covered by their own targeted tests: `project` examples
# (analytic edges have no circle/curve type) and multi-loop `pattern` examples (disjoint
# loops; a multi-loop face is deferred until WireOrderer supports multiple loops).
_FAKE_KERNEL_SKIP = ("project", "op = pattern")
_FAKE_KERNEL_DOCS = [p for p in _EXAMPLE_DOCS
                     if not any(token in p.read_text() for token in _FAKE_KERNEL_SKIP)]


def test_examples_exist() -> None:
    assert _EXAMPLE_DOCS, "no gate example documents found under examples/gate-*/"


@pytest.mark.parametrize("doc_path", _FAKE_KERNEL_DOCS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_example_builds_without_issues(doc_path: Path) -> None:
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc_path))

    assert results, f"{doc_path} produced no parts"
    for name, result in results.items():
        errors = [i for i in result.issues if i.level == "error"]
        assert errors == [], f"{doc_path} part {name} had errors: {errors}"
        assert result.shape is not None


@pytest.mark.slow
def test_gate_0_1_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-0.1-first-shape" / "block.hocon"

    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["block"])
    assert glb.is_file() and glb.stat().st_size > 0


@pytest.mark.slow
def test_gate_0_2_bracket_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-0.2" / "bracket.hocon"

    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["bracket"])
    assert glb.is_file() and glb.stat().st_size > 0


@pytest.mark.slow
def test_gate_0_2_hex_boss_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-0.2" / "hex_boss.hocon"

    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["hex_boss"])
    assert glb.is_file() and glb.stat().st_size > 0


@pytest.mark.slow
def test_gate_0_3_exports_glb_and_elementmap(tmp_path) -> None:
    import json

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-0.3" / "selector_fillet.hocon"
    builder = DocumentBuilder(Build123dKernel())
    artifacts = builder.build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["selector_fillet"])
    assert glb.is_file() and glb.stat().st_size > 0
    sidecar = tmp_path / "selector_fillet.elementmap.json"
    assert sidecar.is_file()
    data = json.loads(sidecar.read_text())
    assert data["elements"]


@pytest.mark.slow
def test_gate_0_3_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden_path = Path(__file__).resolve().parents[1] / "build" / "golden" / \
        "selector_fillet.signature.json"
    golden = json.loads(golden_path.read_text())

    builder = DocumentBuilder(Build123dKernel())
    resolved = builder._resolve_and_validate(
        builder._loader.load(str(_EXAMPLES_DIR / "gate-0.3" / "selector_fillet.hocon")))
    result, _ = builder._builder.build_part_mapped(resolved["parts"]["selector_fillet"])
    live = Build123dKernel().signature(result.shape)

    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
