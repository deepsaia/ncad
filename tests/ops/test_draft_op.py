from ncad.ops.draft_op import DraftOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def test_draft_tapers_the_solid():
    k = FakeKernel()
    box = _box(k)
    result = DraftOp().build(
        box, {"id": "dr", "angle": 5, "__refs__": {"faces": ["f1", "f2"]}}, {}, k)
    assert result.shape is not None
    assert 0 < k.volume(result.shape) < k.volume(box)


def test_draft_missing_solid_reports_issue():
    k = FakeKernel()
    result = DraftOp().build(
        None, {"id": "dr", "angle": 5, "__refs__": {"faces": ["f1"]}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_draft_no_faces_reports_issue():
    k = FakeKernel()
    box = _box(k)
    result = DraftOp().build(box, {"id": "dr", "angle": 5, "__refs__": {"faces": []}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_draft_bad_angle_reports_issue():
    k = FakeKernel()
    box = _box(k)
    result = DraftOp().build(
        box, {"id": "dr", "angle": 0, "__refs__": {"faces": ["f1"]}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
