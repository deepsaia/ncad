import pytest

pytestmark = pytest.mark.slow


def _box(kernel, s=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def _top_face(kernel, solid):
    faces = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"]
    return max(faces, key=lambda d: d["mid_z"])["handle"]


def test_move_face_outward_grows_volume() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = _box(kernel)
    before = kernel.volume(box)
    moved = kernel.move_face(box, _top_face(kernel, box), 3.0)
    assert kernel.volume(moved) > before


def test_move_face_inward_shrinks_volume() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = _box(kernel)
    before = kernel.volume(box)
    moved = kernel.move_face(box, _top_face(kernel, box), -3.0)
    assert kernel.volume(moved) < before
