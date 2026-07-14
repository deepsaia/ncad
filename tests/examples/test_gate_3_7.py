"""End-to-end coverage for bucket 3.7 (Phase 3 completeness) gate parts.

Real parts exercising pattern drivers (circular + suppress, fill), per-body materials, the
inertia tensor, and baked per-body glTF colors. Each builds on the real kernel (slow),
round-trips to STEP, and matches a golden geometry signature.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-3.7"
_GOLDEN = Path(__file__).resolve().parents[1] / "build" / "golden"
_PARTS = ["bolt_circle_flange", "pin_heatsink", "bimetal_bushing"]


@pytest.mark.parametrize("name", _PARTS)
def test_gate_3_7_builds_and_step_round_trips(name, tmp_path):
    from build123d import import_step

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    artifacts = DocumentBuilder(Build123dKernel()).build_file(
        str(_DIR / f"{name}.hocon"), str(tmp_path), formats=("step",))
    step_path = Path(artifacts[name])
    assert step_path.is_file()
    assert abs(import_step(str(step_path)).volume) > 0


@pytest.mark.parametrize("name", _PARTS)
def test_gate_3_7_signature_matches_golden(name):
    from ncad.build.equality_comparator import EqualityComparator

    golden = json.loads((_GOLDEN / f"{name}.signature.json").read_text())
    live = _signature(name)
    comparator = EqualityComparator()
    assert comparator.equal(live, golden), comparator.explain(live, golden)


def test_bolt_circle_has_six_bolt_holes():
    # 8 circular pattern positions minus 2 suppressed = 6 bolt holes (+ bore + outer wall).
    kernel, sig = _kernel_signature("bolt_circle_flange")
    assert sig["surface_types"]["cylinder"] == 8   # 6 bolt holes + bore + outer cylinder


def test_bimetal_bushing_is_two_materials():
    # The bushing keeps a steel shell + a bronze liner as two addressable bodies.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.build.material_resolver import MaterialResolver
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.spec.material_library import MaterialLibrary

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    doc = builder._loader.load(str(_DIR / "bimetal_bushing.hocon"))
    resolved = builder._resolve_and_validate(doc)
    part = resolved["parts"]["bimetal_bushing"]
    result, _, _ = builder._builder.build_part_mapped(part)
    resolver = MaterialResolver(part, MaterialLibrary(doc, base_dir=str(_DIR)))
    materials = {resolver.material_name(b) for b in kernel.bodies(result.shape)}
    assert materials == {"steel_1018", "bronze"}


def _signature(name: str) -> dict:
    _kernel, sig = _kernel_signature(name)
    return sig


def _kernel_signature(name: str):
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(
        builder._loader.load(str(_DIR / f"{name}.hocon")))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"][name])
    assert result.shape is not None
    return kernel, kernel.signature(result.shape)
