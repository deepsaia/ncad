import pytest

from ncad.ops.sketch_op import SketchOp
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

    result = SketchOp().build(None, _rect_feature(), {}, kernel)

    assert result.issues == []
    # A rectangle face extruded by 1 gives volume == area.
    solid = kernel.extrude(result.shape, 1.0)
    assert kernel.volume(solid) == 80.0 * 60.0


def test_sketch_records_provenance_for_the_feature() -> None:
    kernel = FakeKernel()

    result = SketchOp().build(None, _rect_feature(), {}, kernel)

    assert result.provenance.get("sk") == "sketch"


def test_sketch_with_unknown_element_reports_issue_by_id() -> None:
    kernel = FakeKernel()
    feature = _rect_feature()
    feature["elements"][0]["type"] = "trapezoid"

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "sk"


def test_sketch_circle_area() -> None:
    import math

    kernel = FakeKernel()
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "elements": [{"id": "c", "type": "circle", "d": 20.0}]}

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.issues == []
    area = kernel.volume(kernel.extrude(result.shape, 1.0))
    assert area == pytest.approx(math.pi * 100.0, rel=0.02)


def test_sketch_polygon_from_points() -> None:
    kernel = FakeKernel()
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "elements": [{"id": "p", "type": "polygon",
                             "points": [[0, 0], [40, 0], [40, 30], [0, 30]]}]}

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.issues == []
    assert kernel.volume(kernel.extrude(result.shape, 1.0)) == pytest.approx(1200.0)
