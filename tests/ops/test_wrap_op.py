from ncad.ops.wrap_op import WrapOp
from tests.kernel.fake_kernel import FakeKernel


def _plate(k):
    return k.extrude(k.polygon_face([(0, 0), (40, 0), (40, 40), (0, 40)], "XY"),
                     distance=10.0)


class _FaceElement:
    def __init__(self) -> None:
        self.handle = object()


def _profile(k):
    return k.polygon_face([(0, 0), (6, 0), (6, 4), (0, 4)], "XY")


def test_wrap_text_emboss_routes():
    k = FakeKernel()
    plate = _plate(k)
    result = WrapOp().build(
        plate, {"id": "w", "text": "AB", "depth": 1, "mode": "emboss",
                "__refs__": {"on": _FaceElement()}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) > k.volume(plate)


def test_wrap_profile_engrave_routes():
    k = FakeKernel()
    plate = _plate(k)
    result = WrapOp().build(
        plate, {"id": "w", "depth": 1, "mode": "engrave",
                "__refs__": {"on": _FaceElement(), "profile": _profile(k)}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) < k.volume(plate)


def test_wrap_missing_solid_reports_issue():
    k = FakeKernel()
    result = WrapOp().build(
        None, {"id": "w", "text": "A", "depth": 1,
               "__refs__": {"on": _FaceElement()}}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_wrap_missing_face_reports_issue():
    k = FakeKernel()
    plate = _plate(k)
    result = WrapOp().build(plate, {"id": "w", "text": "A", "depth": 1, "__refs__": {}}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_wrap_both_text_and_profile_reports_issue():
    k = FakeKernel()
    plate = _plate(k)
    result = WrapOp().build(
        plate, {"id": "w", "text": "A", "depth": 1,
                "__refs__": {"on": _FaceElement(), "profile": _profile(k)}}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_wrap_neither_text_nor_profile_reports_issue():
    k = FakeKernel()
    plate = _plate(k)
    result = WrapOp().build(
        plate, {"id": "w", "depth": 1, "__refs__": {"on": _FaceElement()}}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
