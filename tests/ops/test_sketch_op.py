from ncad.ops.sketch_op import build_sketch
from tests.kernel.fake_kernel import FakeKernel


def _rect_feature() -> dict:
    return {
        "id": "sk",
        "op": "sketch",
        "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
    }


def test_sketch_builds_a_face_with_expected_area() -> None:
    kernel = FakeKernel()

    result = build_sketch(None, _rect_feature(), {}, kernel)

    assert result.issues == []
    # A rectangle face extruded by 1 gives volume == area.
    solid = kernel.extrude(result.shape, 1.0)
    assert kernel.volume(solid) == 80.0 * 60.0


def test_sketch_records_provenance_for_the_feature() -> None:
    kernel = FakeKernel()

    result = build_sketch(None, _rect_feature(), {}, kernel)

    assert result.provenance.get("sk") == "sketch"


def test_sketch_with_unknown_element_reports_issue_by_id() -> None:
    kernel = FakeKernel()
    feature = _rect_feature()
    feature["elements"][0]["type"] = "trapezoid"

    result = build_sketch(None, feature, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "sk"
