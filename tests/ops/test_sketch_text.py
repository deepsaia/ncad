from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def test_sketch_text_element_builds_a_face():
    params = {
        "id": "label", "plane": "XY",
        "elements": [{"id": "t", "type": "text", "text": "NC", "font_size": 8.0}],
    }
    result = SketchOp().build(None, params, {}, FakeKernel())
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
    assert result.status_report is not None and result.status_report.status == "well"
