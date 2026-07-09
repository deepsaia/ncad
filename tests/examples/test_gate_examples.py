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
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["selector_fillet"])
    live = Build123dKernel().signature(result.shape)

    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


@pytest.mark.slow
def test_gate_2_9_bracket_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-2.9" / "mounting_bracket.hocon"

    def _signature() -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(
            resolved["parts"]["mounting_bracket"])
        assert result.shape is not None
        return kernel.signature(result.shape)

    sig1, sig2 = _signature(), _signature()
    comparator = EqualityComparator()
    assert comparator.equal(sig1, sig2), comparator.explain(sig1, sig2)


@pytest.mark.slow
def test_gate_2_9_bracket_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden_path = Path(__file__).resolve().parents[1] / "build" / "golden" / \
        "mounting_bracket.signature.json"
    golden = json.loads(golden_path.read_text())

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-2.9" / "mounting_bracket.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["mounting_bracket"])
    live = kernel.signature(result.shape)

    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


@pytest.mark.slow
def test_gate_2_9_bracket_step_round_trips(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-2.9" / "mounting_bracket.hocon"
    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["mounting_bracket"])
    assert step_path.is_file()
    # Validity is by measure magnitude (design section 4a), not orientation sign.
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.slow
def test_gate_2_9_bracket_composes_additively_step_by_step() -> None:
    """Every prefix of the feature stack builds to a valid single solid.

    The feature tree is a stateful pipeline (like a Blender modifier stack): each op
    consumes the previous op's result. This truncates the bracket to the first N features
    and asserts each cumulative stack is a valid solid, proving the ops compose additively
    in sequence (not just in isolation). A fresh load per prefix avoids shared-state
    mutation. A `sketch` feature originates no solid, so it carries the prior solid forward;
    every feature that outputs a solid must yield exactly one valid solid.
    """
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = str(_EXAMPLES_DIR / "gate-2.9" / "mounting_bracket.hocon")
    builder = DocumentBuilder(Build123dKernel())
    feature_count = len(
        builder._resolve_and_validate(builder._loader.load(doc))
        ["parts"]["mounting_bracket"]["features"])

    prev_shape = None
    for n in range(1, feature_count + 1):
        resolved = builder._resolve_and_validate(builder._loader.load(doc))
        part = resolved["parts"]["mounting_bracket"]
        last_op = part["features"][n - 1].get("op", "")
        part["features"] = part["features"][:n]
        result, _, _ = builder._builder.build_part_mapped(part)
        errors = [i for i in result.issues if i.level == "error"]
        assert errors == [], f"prefix of {n} features (last op {last_op!r}) errored: {errors}"
        if last_op == "sketch":
            continue  # a sketch originates no solid; the running solid is unchanged
        assert result.shape is not None, f"prefix of {n} features produced no shape"
        solids = result.shape.solids()
        assert len(solids) == 1, f"prefix of {n} features is {len(solids)} solids, not one"
        assert result.shape.is_valid, f"prefix of {n} features is an invalid B-rep"
        prev_shape = result.shape
    assert prev_shape is not None


@pytest.mark.slow
def test_gate_3_0_two_body_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.0" / "two_body_bracket.hocon"

    def _signature() -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(
            resolved["parts"]["two_body_bracket"])
        assert result.shape is not None
        return kernel.signature(result.shape)

    sig1, sig2 = _signature(), _signature()
    comparator = EqualityComparator()
    assert comparator.equal(sig1, sig2), comparator.explain(sig1, sig2)


@pytest.mark.slow
def test_gate_3_0_two_body_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden_path = Path(__file__).resolve().parents[1] / "build" / "golden" / \
        "two_body_bracket.signature.json"
    golden = json.loads(golden_path.read_text())

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.0" / "two_body_bracket.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["two_body_bracket"])
    live = kernel.signature(result.shape)

    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


@pytest.mark.slow
def test_gate_3_0_two_body_step_round_trips_as_two_solids(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.0" / "two_body_bracket.hocon"
    kernel = Build123dKernel()
    artifacts = DocumentBuilder(kernel).build_file(str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["two_body_bracket"])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0
    # The built part is a 2-body BodySet (kept separate by merge = false).
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["two_body_bracket"])
    assert len(kernel.bodies(result.shape)) == 2


@pytest.mark.slow
def test_gate_3_1_transformed_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.1" / "transformed_blocks.hocon"

    def _signature() -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(
            resolved["parts"]["transformed_blocks"])
        assert result.shape is not None
        return kernel.signature(result.shape)

    sig1, sig2 = _signature(), _signature()
    comparator = EqualityComparator()
    assert comparator.equal(sig1, sig2), comparator.explain(sig1, sig2)


@pytest.mark.slow
def test_gate_3_1_transformed_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden_path = Path(__file__).resolve().parents[1] / "build" / "golden" / \
        "transformed_blocks.signature.json"
    golden = json.loads(golden_path.read_text())

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.1" / "transformed_blocks.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["transformed_blocks"])
    live = kernel.signature(result.shape)

    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


@pytest.mark.slow
def test_gate_3_1_transformed_step_round_trips_as_two_solids(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.1" / "transformed_blocks.hocon"
    kernel = Build123dKernel()
    artifacts = DocumentBuilder(kernel).build_file(str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["transformed_blocks"])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["transformed_blocks"])
    assert len(kernel.bodies(result.shape)) == 2
