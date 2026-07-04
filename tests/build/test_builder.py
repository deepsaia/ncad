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
    result, element_map = Builder(
        FakeKernel(), OpRegistry.with_defaults()).build_part_mapped(part)
    assert result.shape is not None
    assert element_map.by_tag("cap(+Z)"), "extrude should tag a +Z cap"
