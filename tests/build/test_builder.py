from ncad.build.builder import Builder
from ncad.ops.op_registry import OpRegistry
from tests.kernel.fake_kernel import FakeKernel


def _block_part() -> dict:
    return {
        "profile": "solid",
        "features": [
            {
                "id": "sk",
                "op": "sketch",
                "plane": "XY",
                "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
            },
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
        ],
    }


def test_builder_produces_solid_with_expected_volume() -> None:
    builder = Builder(FakeKernel(), OpRegistry.with_defaults())

    result = builder.build_part(_block_part())

    assert result.issues == []
    assert FakeKernel().volume(result.shape) == 80.0 * 60.0 * 8.0


def test_builder_extrude_consumes_named_profile_not_previous_feature() -> None:
    # A second sketch ('other', 40x40) is threaded between 'sk' and 'pad'. Because
    # 'pad' names profile 'sk', it must extrude the 80x60 face (volume 80*60*8),
    # NOT the immediately-preceding 40x40 face. This proves named-profile resolution
    # rather than blind previous-shape threading.
    kernel = FakeKernel()
    builder = Builder(kernel, OpRegistry.with_defaults())
    part = {
        "profile": "solid",
        "features": [
            {
                "id": "sk",
                "op": "sketch",
                "plane": "XY",
                "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
            },
            {
                "id": "other",
                "op": "sketch",
                "plane": "XY",
                "elements": [{"id": "r2", "type": "rectangle", "w": 40.0, "h": 40.0}],
            },
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
        ],
    }

    result = builder.build_part(part)

    assert result.issues == []
    assert kernel.volume(result.shape) == 80.0 * 60.0 * 8.0


def test_builder_reports_issue_when_referenced_profile_missing() -> None:
    builder = Builder(FakeKernel(), OpRegistry.with_defaults())
    part = _block_part()
    part["features"][1]["profile"] = "does_not_exist"

    result = builder.build_part(part)

    assert any(issue.node_id == "pad" for issue in result.issues)


def _rect(id_, w, h):
    return {"id": id_, "op": "sketch", "plane": "XY",
            "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}


def test_fillet_by_selector_resolves_edges() -> None:
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 2,
         "edges": "select edges where created_by='pad' and orientation='vertical'"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.issues == [] and result.shape is not None


def test_generative_cap_ref_on_hole_resolves() -> None:
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
        {"id": "h", "op": "hole", "on": "pad.cap(+Z)", "diameter": 4,
         "depth": 5, "positions": [[10, 10]]},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.issues == [] and result.shape is not None


def test_unresolvable_reference_is_id_tagged_issue() -> None:
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 2,
         "edges": "select edges where created_by='ghost'"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert any(i.node_id == "rnd" for i in result.issues)


def test_keyword_edges_still_work() -> None:
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 2, "edges": "vertical"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.issues == [] and result.shape is not None


def test_build_part_mapped_returns_element_map() -> None:
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
    ]}
    result, element_map, _ = Builder(
        FakeKernel(), OpRegistry.with_defaults()).build_part_mapped(part)
    assert result.shape is not None
    assert element_map.by_tag("cap(+Z)"), "extrude should tag a +Z cap"


def test_cache_hit_skips_reexecution() -> None:
    from ncad.build.feature_cache import FeatureCache

    kernel = FakeKernel()
    cache = FeatureCache()
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
    ]}
    builder = Builder(kernel, OpRegistry.with_defaults(), cache=cache)

    builder.build_part_mapped(part)
    first = cache.stats()
    builder.build_part_mapped(part)
    second = cache.stats()

    assert first == {"sk": False, "pad": False}
    assert second == {"sk": True, "pad": True}


def test_param_edit_rebuilds_only_dirty_suffix() -> None:
    from ncad.build.feature_cache import FeatureCache

    kernel = FakeKernel()
    cache = FeatureCache()
    builder = Builder(kernel, OpRegistry.with_defaults(), cache=cache)

    def part(distance):
        return {"profile": "solid", "features": [
            _rect("sk", 40, 40),
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": distance},
            {"id": "h", "op": "hole", "diameter": 4, "depth": 3, "positions": [[10, 10]]},
        ]}

    builder.build_part_mapped(part(10))
    builder.build_part_mapped(part(12))
    stats = cache.stats()

    assert stats == {"sk": True, "h": False, "pad": False}


def test_cache_hit_preserves_generative_tags() -> None:
    from ncad.build.feature_cache import FeatureCache

    kernel = FakeKernel()
    cache = FeatureCache()
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
    ]}
    builder = Builder(kernel, OpRegistry.with_defaults(), cache=cache)

    builder.build_part_mapped(part)
    _, element_map, _ = builder.build_part_mapped(part)

    assert element_map.by_tag("cap(+Z)"), "cached rebuild must restore generative tags"


def test_warning_issue_does_not_mark_feature_failed() -> None:
    from ncad.build.feature_cache import FeatureCache
    from ncad.ops.build_issue import BuildIssue
    from ncad.ops.op_result import OpResult

    kernel = FakeKernel()
    solid = kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 5.0)

    def warn_op(shape_in, params, prov, k):
        return OpResult(shape=solid, provenance={},
                        issues=[BuildIssue(node_id=params["id"], message="w", level="warning")])

    def after_op(shape_in, params, prov, k):
        # succeeds only if it received the warn feature's shape (not suppressed)
        return OpResult(shape=shape_in, provenance={}, issues=[])

    reg = OpRegistry()
    reg.register("warn", warn_op)
    reg.register("after", after_op)
    part = {"profile": "solid", "features": [
        {"id": "w", "op": "warn"}, {"id": "a", "op": "after"}]}
    result, _, _ = Builder(kernel, reg, cache=FeatureCache()).build_part_mapped(part)

    assert result.shape is solid
    assert not any("depends on failed" in i.message for i in result.issues)


def test_sketch_project_field_resolves_to_refs() -> None:
    from ncad.ops.op_result import OpResult

    captured = {}

    def probe(shape_in, params, prov, kernel):
        # capture refs only for the feature that declares a project field
        if "project" in params:
            captured["refs"] = params.get("__refs__", {})
        # sketches must still produce a solid-ish shape for downstream; reuse a fake face
        if params.get("project") is None and "elements" in params:
            return SketchOpReal().build(shape_in, params, prov, kernel)
        return OpResult(shape=None, provenance={}, issues=[])

    from ncad.ops.sketch_op import SketchOp as SketchOpReal
    reg = OpRegistry.with_defaults()
    reg.register("sketch", probe)
    part = {"profile": "solid", "features": [
        _rect("base", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "base", "distance": 5},
        {"id": "sk2", "op": "sketch", "plane": "XY",
         "project": ["select edges where created_by='pad'"]},
    ]}
    Builder(FakeKernel(), reg).build_part_mapped(part)
    assert "project" in captured["refs"]
    assert isinstance(captured["refs"]["project"], list)


def test_build_part_mapped_returns_sketch_statuses() -> None:
    result, _element_map, statuses = Builder(
        FakeKernel(), OpRegistry.with_defaults()).build_part_mapped(_block_part())
    assert result.shape is not None
    # only the sketch feature contributes a status; the extrude does not
    assert [s.feature_id for s in statuses] == ["sk"]
    assert statuses[0].status == "well"
