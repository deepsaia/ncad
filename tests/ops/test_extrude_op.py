from ncad.ops.extrude_op import build_extrude
from ncad.ops.sketch_op import build_sketch
from tests.kernel.fake_kernel import FakeKernel


def _rect_feature() -> dict:
    return {
        "id": "sk",
        "op": "sketch",
        "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
    }


def test_extrude_produces_solid_with_expected_volume() -> None:
    kernel = FakeKernel()
    face = build_sketch(None, _rect_feature(), {}, kernel).shape

    result = build_extrude(face, {"id": "pad", "op": "extrude", "distance": 8.0}, {}, kernel)

    assert result.issues == []
    assert kernel.volume(result.shape) == 80.0 * 60.0 * 8.0
    assert result.provenance.get("pad") == "extrude"


def test_extrude_without_input_shape_reports_issue_by_id() -> None:
    kernel = FakeKernel()

    result = build_extrude(None, {"id": "pad", "op": "extrude", "distance": 8.0}, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "pad"
