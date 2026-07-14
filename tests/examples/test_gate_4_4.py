"""End-to-end coverage for bucket 4.4 (Phase 4 completeness) capstone gate parts.

Real, recognizable parts exercising the 4.4 features:
  - mounting_cover: a bolt-circle end cap whose 6 counterbored holes are drilled by a FEATURE
    PATTERN (pattern the cut's effect, not a body).
  - mirrored_hinge: a hinge leaf whose reinforcing strap boss is MIRRORED across a plane, plus a
    separate pin body moved COAXIAL to the knuckle bore (multibody-moving relate).
  - curved_import_edit: an imported spline-topped solid whose curved top edge is PROJECTED into a
    sketch (curved-edge projection on foreign geometry), with names surviving a rebuild.
Each builds on the real kernel (slow).
"""

import copy
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_DIR = Path(__file__).resolve().parents[2] / "examples" / "gate-4.4"


def _build(name: str):
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(
        builder._loader.load(str(_DIR / f"{name}.hocon")))
    result, element_map, _ = builder._builder.build_part_mapped(resolved["parts"][name])
    return kernel, result, element_map


def test_mounting_cover_feature_patterns_six_counterbores():
    kernel, result, _ = _build("mounting_cover")
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    sig = kernel.signature(result.shape)
    # 1 central bore + 6 bolt-hole shafts + 6 counterbore steps + the outer cylinder = 14.
    assert sig["surface_types"]["cylinder"] == 14


def test_mirrored_hinge_is_two_bodies_with_pin_seated():
    from ncad.kernel.body_set import BodySet

    kernel, result, _ = _build("mirrored_hinge")
    assert isinstance(result.shape, BodySet)
    assert not [i for i in result.issues if i.level == "error"]
    ids = result.shape.ids()
    assert ids == ["assembly/body/0", "assembly/body/1"]
    # The pin body (body/1) was moved coaxial to the knuckle bore: its x-extent now sits at the
    # knuckle (negative x), not its authored +x sketch position.
    pin = result.shape.by_id("assembly/body/1")
    (minx, _, _), (maxx, _, _) = kernel.bounding_box(pin.shape)
    assert maxx < 0.0


def _write_curved_input(kernel, path: str) -> None:
    """Export the spline-topped source solid the curved_import_edit example imports."""
    from ncad.build.builder import Builder
    from ncad.ops.op_registry import OpRegistry

    source = {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY", "entities": [
            {"id": "p0", "type": "point", "at": [0, 0]},
            {"id": "pm", "type": "point", "at": [20, 12]},
            {"id": "p1", "type": "point", "at": [40, 0]},
            {"id": "p2", "type": "point", "at": [40, -20]},
            {"id": "p3", "type": "point", "at": [0, -20]},
            {"id": "top", "type": "interpolated", "points": ["p0", "pm", "p1"]},
            {"id": "r", "type": "line", "p1": "p1", "p2": "p2"},
            {"id": "bt", "type": "line", "p1": "p2", "p2": "p3"},
            {"id": "l", "type": "line", "p1": "p3", "p2": "p0"}],
         "constraints": [{"type": "fix", "of": "p0"}, {"type": "fix", "of": "pm"},
            {"type": "fix", "of": "p1"}, {"type": "fix", "of": "p2"}, {"type": "fix", "of": "p3"}]},
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8}]}
    builder = Builder(kernel, OpRegistry.with_defaults())
    src, _, _ = builder.build_part_mapped(source)
    kernel.export(src.shape, path)


def test_curved_import_edit_projects_a_spline_edge(tmp_path):
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry
    from ncad.spec.spec_loader import SpecLoader

    kernel = Build123dKernel()
    step = tmp_path / "curved_import_edit_input.step"
    _write_curved_input(kernel, str(step))

    document = SpecLoader().load(str(_DIR / "curved_import_edit.hocon"))
    part = copy.deepcopy(document["parts"]["curved_import_edit"])
    for feature in part["features"]:
        if feature["op"] == "import":
            feature["file"] = str(step)

    builder = Builder(kernel, OpRegistry.with_defaults())
    result, element_map, statuses = builder.build_part_mapped(copy.deepcopy(part))
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    # The sketch that projects the imported spline top edge solves cleanly (curved-edge
    # projection on foreign geometry no longer refused).
    scribe = next(s for s in statuses if s.feature_id == "scribe_sk")
    assert scribe.status == "well"
    # Rebuilding the same imported part yields identical persistent names (names survive).
    _result2, element_map2, _ = builder.build_part_mapped(copy.deepcopy(part))
    ids1 = {e.id for e in element_map.elements()}
    ids2 = {e.id for e in element_map2.elements()}
    assert ids1 == ids2 and len(ids1) > 0
