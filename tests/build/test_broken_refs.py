from ncad.build.builder import Builder
from ncad.build.feature_cache import FeatureCache
from ncad.ops.op_registry import OpRegistry
from tests.kernel.fake_kernel import FakeKernel


def _rect(id_, w, h):
    return {"id": id_, "op": "sketch", "plane": "XY",
            "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}


def _bracket(extrude_profile="sk"):
    return {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": extrude_profile, "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 3,
         "edges": "select edges where created_by='pad' and orientation='vertical'"},
    ]}


def test_missing_profile_yields_one_primary_and_one_downstream_issue():
    part = _bracket(extrude_profile="ghost")
    result, _ = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part_mapped(part)

    by_id: dict = {}
    for issue in result.issues:
        by_id.setdefault(issue.node_id, []).append(issue.message)
    assert list(by_id) == ["pad", "rnd"]
    assert len(by_id["pad"]) == 1
    assert len(by_id["rnd"]) == 1
    assert "depends on failed feature pad" in by_id["rnd"][0]


def test_dressup_over_missing_solid_reports_depends_on_failed():
    part = {"profile": "solid", "features": [
        _rect("sk", 40, 40),
        {"id": "pad", "op": "extrude", "profile": "missing", "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 3, "edges": "vertical"},
    ]}
    result, _ = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part_mapped(part)
    rnd = [i for i in result.issues if i.node_id == "rnd"]
    assert len(rnd) == 1 and "depends on failed feature pad" in rnd[0].message


def test_failed_feature_is_not_cached_and_reports_each_build():
    cache = FeatureCache()
    builder = Builder(FakeKernel(), OpRegistry.with_defaults(), cache=cache)
    part = _bracket(extrude_profile="ghost")

    first, _ = builder.build_part_mapped(part)
    second, _ = builder.build_part_mapped(part)

    def ids(result):
        return sorted({i.node_id for i in result.issues})
    assert ids(first) == ["pad", "rnd"]
    assert ids(second) == ["pad", "rnd"]


def test_fixing_the_doc_clears_the_issue_and_caches():
    cache = FeatureCache()
    builder = Builder(FakeKernel(), OpRegistry.with_defaults(), cache=cache)

    broken, _ = builder.build_part_mapped(_bracket(extrude_profile="ghost"))
    assert broken.issues

    fixed, _ = builder.build_part_mapped(_bracket(extrude_profile="sk"))
    assert fixed.issues == [] and fixed.shape is not None
