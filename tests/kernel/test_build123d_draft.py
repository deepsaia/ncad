import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def _vertical_faces(k, box):
    from ncad.ops.face_selector import FaceSelector
    faces = [d for d in k.describe_elements(box) if d["kind"] == "face"]
    return FaceSelector().select(faces, "vertical")


def test_draft_vertical_faces_builds():
    k = _kernel()
    box = _box(k)
    result = k.draft(box, _vertical_faces(k, box), angle=5.0, neutral="XY",
                     neutral_offset=0.0)
    assert k.volume(result) > 0


def test_draft_with_neutral_offset_builds():
    k = _kernel()
    box = _box(k)
    result = k.draft(box, _vertical_faces(k, box), angle=5.0, neutral="XY",
                     neutral_offset=10.0)
    assert k.volume(result) > 0
