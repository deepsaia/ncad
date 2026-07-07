import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def test_closed_shell_builds_hollow():
    k = _kernel()
    box = _box(k)
    v0 = k.volume(box)
    result = k.shell(box, 2.0)
    assert 0 < k.volume(result) < v0


def test_open_shell_removes_a_face():
    k = _kernel()
    box = _box(k)
    faces = [d for d in k.describe_elements(box) if d["kind"] == "face"]
    from ncad.ops.face_selector import FaceSelector
    top = FaceSelector().select(faces, "top")
    result = k.shell(box, 2.0, openings=top)
    # An open shell removes more material than a closed one (the opening + its cavity).
    assert 0 < k.volume(result) < k.volume(k.shell(box, 2.0))
