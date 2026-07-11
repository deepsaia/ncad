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
# (analytic edges have no circle/curve type) and multi-loop SKETCH `pattern` transforms
# (discriminated by `sources =`; disjoint loops need multi-loop faces, deferred until
# WireOrderer supports multiple loops). The feature-level `pattern` op (gate-3.2) is NOT
# a sketch transform and builds fine on the FakeKernel, so it stays in the sweep.
_FAKE_KERNEL_SKIP = ("project", "sources =")
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


def test_gate_3_2_pattern_volumes_on_fake_kernel() -> None:
    doc = _EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon"
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc))

    studs = results["pattern_studs"]
    assert [i for i in studs.issues if i.level == "error"] == []
    # 12 studs of 6*6*10 = 360 each, kept separate.
    assert FakeKernel().volume(studs.shape) == pytest.approx(12 * 360.0)
    assert len(FakeKernel().bodies(studs.shape)) == 12

    hub = results["spoke_hub"]
    assert [i for i in hub.issues if i.level == "error"] == []
    # 6 spokes of 24*4*6 = 576 each; FakeKernel fuse sums (no overlap subtraction).
    assert FakeKernel().volume(hub.shape) == pytest.approx(6 * 576.0)


def test_gate_3_3_mirror_volumes_on_fake_kernel() -> None:
    doc = _EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon"
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc))

    bracket = results["symmetric_bracket"]
    assert [i for i in bracket.issues if i.level == "error"] == []
    # L-area = 20*6 + 6*14 = 204; extruded 8 -> 1632 per side; fused fake-volume = 2 * 1632.
    assert FakeKernel().volume(bracket.shape) == pytest.approx(2 * 1632.0)

    pair = results["mirror_pair"]
    assert [i for i in pair.issues if i.level == "error"] == []
    # boss 10*8*6 = 480 each; kept separate -> 2 bodies, total 960.
    assert FakeKernel().volume(pair.shape) == pytest.approx(2 * 480.0)
    assert len(FakeKernel().bodies(pair.shape)) == 2
    assert FakeKernel().bodies(pair.shape)[0].id == "pair/body/0"


def test_gate_3_4_multibody_algebra_on_fake_kernel() -> None:
    doc = _EXAMPLES_DIR / "gate-3.4" / "multibody_algebra.hocon"
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc))

    halves = results["split_block"]
    assert [i for i in halves.issues if i.level == "error"] == []
    assert len(FakeKernel().bodies(halves.shape)) == 2
    assert FakeKernel().volume(halves.shape) == pytest.approx(20 * 10 * 8)

    drilled = results["multi_cut"]
    assert [i for i in drilled.issues if i.level == "error"] == []
    # plate 40*20*6 = 4800 minus three 4*4*6 = 96 tools -> 4512; single body.
    assert len(FakeKernel().bodies(drilled.shape)) == 1
    assert FakeKernel().volume(drilled.shape) == pytest.approx(4800.0 - 3 * 96.0)

    merged = results["scoped_merge"]
    assert [i for i in merged.issues if i.level == "error"] == []
    ids = {b.id for b in FakeKernel().bodies(merged.shape)}
    assert ids == {"merged/body/0", "row/body/1"}
    # 3 studs of 6*6*10 = 360; union of 0+2 = 720, plus passthrough 360 -> 1080 total.
    assert FakeKernel().volume(merged.shape) == pytest.approx(3 * 360.0)


def test_gate_3_5_materials_mass_on_fake_kernel() -> None:
    from ncad.build.mass_calculator import MassCalculator
    from ncad.build.material_resolver import MaterialResolver
    from ncad.spec.material_library import MaterialLibrary

    builder = DocumentBuilder(FakeKernel())
    doc = builder._loader.load(str(_EXAMPLES_DIR / "gate-3.5" / "materials_part.hocon"))
    part = builder._resolve_and_validate(doc)["parts"]["materials_part"]
    result, _, _ = builder._builder.build_part_mapped(part)
    assert [i for i in result.issues if i.level == "error"] == []

    lib = MaterialLibrary(doc, base_dir=str(_EXAMPLES_DIR / "gate-3.5"))
    resolver = MaterialResolver(part, lib)
    props = MassCalculator(FakeKernel()).mass_properties(result.shape, resolver)
    # Two materials across bodies: aluminium halves + a steel boss.
    materials = {b["material"] for b in props["bodies"]}
    assert "steel_1018" in materials and "aluminium_6061" in materials
    # Every body's mass = density * volume * 1e-9.
    for b in props["bodies"]:
        assert b["mass"] == pytest.approx(b["density"] * b["volume"] * 1e-9)
    # Assembly total mass = sum of body masses; raw mat_data queryable per body.
    assert props["total"]["mass"] == pytest.approx(sum(b["mass"] for b in props["bodies"]))
    for body in FakeKernel().bodies(result.shape):
        assert resolver.for_body(body)["physical"]["density"] > 0


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


@pytest.mark.slow
def test_gate_3_2_studs_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                         "pattern_studs.signature.json").read_text())
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["pattern_studs"])
    live = kernel.signature(result.shape)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
    assert len(kernel.bodies(result.shape)) == 12


@pytest.mark.slow
def test_gate_3_2_spoke_hub_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                         "spoke_hub.signature.json").read_text())
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["spoke_hub"])
    live = kernel.signature(result.shape)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


@pytest.mark.slow
def test_gate_3_2_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon"

    def _sig(part_name: str) -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(resolved["parts"][part_name])
        assert result.shape is not None
        return kernel.signature(result.shape)

    comparator = EqualityComparator()
    for part_name in ("pattern_studs", "spoke_hub"):
        s1, s2 = _sig(part_name), _sig(part_name)
        assert comparator.equal(s1, s2), comparator.explain(s1, s2)


@pytest.mark.slow
def test_gate_3_2_studs_step_round_trips_as_twelve_solids(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon"
    kernel = Build123dKernel()
    artifacts = DocumentBuilder(kernel).build_file(str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["pattern_studs"])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["pattern_studs"])
    assert len(kernel.bodies(result.shape)) == 12


@pytest.mark.slow
def test_gate_3_2_spoke_hub_composes_additively() -> None:
    """Each feature prefix of the fused spoke_hub builds to a single valid solid."""
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = str(_EXAMPLES_DIR / "gate-3.2" / "patterned_bodies.hocon")
    builder = DocumentBuilder(Build123dKernel())
    feature_count = len(
        builder._resolve_and_validate(builder._loader.load(doc))
        ["parts"]["spoke_hub"]["features"])
    for n in range(1, feature_count + 1):
        resolved = builder._resolve_and_validate(builder._loader.load(doc))
        part = resolved["parts"]["spoke_hub"]
        last_op = part["features"][n - 1].get("op", "")
        part["features"] = part["features"][:n]
        result, _, _ = builder._builder.build_part_mapped(part)
        errors = [i for i in result.issues if i.level == "error"]
        assert errors == [], f"prefix {n} (op {last_op!r}) errored: {errors}"
        if last_op == "sketch":
            continue
        assert result.shape is not None
        solids = result.shape.solids()
        assert len(solids) == 1, f"prefix {n} is {len(solids)} solids, not one"
        assert result.shape.is_valid


@pytest.mark.slow
def test_gate_3_3_bracket_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                         "symmetric_bracket.signature.json").read_text())
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["symmetric_bracket"])
    live = kernel.signature(result.shape)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
    # A fused half-model touching the plane is a single solid.
    assert len(result.shape.solids()) == 1


@pytest.mark.slow
def test_gate_3_3_pair_signature_matches_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                         "mirror_pair.signature.json").read_text())
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["mirror_pair"])
    live = kernel.signature(result.shape)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)
    assert len(kernel.bodies(result.shape)) == 2


@pytest.mark.slow
def test_gate_3_3_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon"

    def _sig(part_name: str) -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(resolved["parts"][part_name])
        assert result.shape is not None
        return kernel.signature(result.shape)

    comparator = EqualityComparator()
    for part_name in ("symmetric_bracket", "mirror_pair"):
        s1, s2 = _sig(part_name), _sig(part_name)
        assert comparator.equal(s1, s2), comparator.explain(s1, s2)


@pytest.mark.slow
def test_gate_3_3_bracket_step_round_trips(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon"
    kernel = Build123dKernel()
    artifacts = DocumentBuilder(kernel).build_file(str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["symmetric_bracket"])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.slow
def test_gate_3_3_bracket_composes_additively() -> None:
    """Each feature prefix of the fused symmetric_bracket builds to a single valid solid."""
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = str(_EXAMPLES_DIR / "gate-3.3" / "mirrored_bodies.hocon")
    builder = DocumentBuilder(Build123dKernel())
    feature_count = len(
        builder._resolve_and_validate(builder._loader.load(doc))
        ["parts"]["symmetric_bracket"]["features"])
    for n in range(1, feature_count + 1):
        resolved = builder._resolve_and_validate(builder._loader.load(doc))
        part = resolved["parts"]["symmetric_bracket"]
        last_op = part["features"][n - 1].get("op", "")
        part["features"] = part["features"][:n]
        result, _, _ = builder._builder.build_part_mapped(part)
        errors = [i for i in result.issues if i.level == "error"]
        assert errors == [], f"prefix {n} (op {last_op!r}) errored: {errors}"
        if last_op == "sketch":
            continue
        assert result.shape is not None
        solids = result.shape.solids()
        assert len(solids) == 1, f"prefix {n} is {len(solids)} solids, not one"
        assert result.shape.is_valid


@pytest.mark.slow
def test_gate_3_4_signatures_match_golden() -> None:
    import json

    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.4" / "multibody_algebra.hocon")))
    comparator = EqualityComparator()
    for name in ("split_block", "multi_cut", "scoped_merge"):
        golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                             f"{name}.signature.json").read_text())
        result, _, _ = builder._builder.build_part_mapped(resolved["parts"][name])
        live = kernel.signature(result.shape)
        assert comparator.equal(live, golden), f"{name}: {comparator.explain(live, golden)}"


@pytest.mark.slow
def test_gate_3_4_builds_twice_deterministically() -> None:
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.4" / "multibody_algebra.hocon"

    def _sig(name: str) -> dict:
        kernel = Build123dKernel()
        builder = DocumentBuilder(kernel)
        resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
        result, _, _ = builder._builder.build_part_mapped(resolved["parts"][name])
        assert result.shape is not None
        return kernel.signature(result.shape)

    comparator = EqualityComparator()
    for name in ("split_block", "multi_cut", "scoped_merge"):
        s1, s2 = _sig(name), _sig(name)
        assert comparator.equal(s1, s2), comparator.explain(s1, s2)


@pytest.mark.slow
def test_gate_3_4_split_block_step_round_trips(tmp_path) -> None:
    from build123d import import_step

    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES_DIR / "gate-3.4" / "multibody_algebra.hocon"
    kernel = Build123dKernel()
    artifacts = DocumentBuilder(kernel).build_file(str(doc), str(tmp_path), formats=("step",))
    step_path = Path(artifacts["split_block"])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.slow
def test_gate_3_4_scoped_merge_bodies() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(builder._loader.load(
        str(_EXAMPLES_DIR / "gate-3.4" / "multibody_algebra.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["scoped_merge"])
    ids = {b.id for b in kernel.bodies(result.shape)}
    assert ids == {"merged/body/0", "row/body/1"}


@pytest.mark.slow
def test_gate_3_5_massprops_match_golden() -> None:
    import json

    from ncad.build.mass_calculator import MassCalculator
    from ncad.build.material_resolver import MaterialResolver
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.spec.material_library import MaterialLibrary

    golden = json.loads((Path(__file__).resolve().parents[1] / "build" / "golden" /
                         "materials_part.massprops.json").read_text())
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    doc = builder._loader.load(str(_EXAMPLES_DIR / "gate-3.5" / "materials_part.hocon"))
    part = builder._resolve_and_validate(doc)["parts"]["materials_part"]
    result, _, _ = builder._builder.build_part_mapped(part)
    lib = MaterialLibrary(doc, base_dir=str(_EXAMPLES_DIR / "gate-3.5"))
    props = MassCalculator(kernel).mass_properties(result.shape, MaterialResolver(part, lib))

    assert len(props["bodies"]) == len(golden["bodies"])
    assert props["total"]["mass"] == pytest.approx(golden["total"]["mass"], rel=1e-6)
    assert props["total"]["volume"] == pytest.approx(golden["total"]["volume"], rel=1e-6)
    for live_b, gold_b in zip(sorted(props["bodies"], key=lambda b: b["id"]),
                              sorted(golden["bodies"], key=lambda b: b["id"])):
        assert live_b["material"] == gold_b["material"]
        assert live_b["mass"] == pytest.approx(gold_b["mass"], rel=1e-6)
