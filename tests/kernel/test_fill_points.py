import pytest

pytestmark = pytest.mark.slow


def test_fill_points_clip_to_a_rectangular_face():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    box = Solid.make_box(40, 24, 5)
    top = next(f for f in box.faces() if f.normal_at().Z > 0.9)
    pts = Build123dKernel().fill_points(top, spacing=8.0, stagger=False)
    assert len(pts) > 4
    assert all(len(p) == 3 for p in pts)


def test_fill_points_clip_to_a_disk_face():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    disk = Solid.make_cylinder(15, 3)
    top = next(f for f in disk.faces() if f.normal_at().Z > 0.9)
    square = Build123dKernel().fill_points(top, spacing=6.0, stagger=False)
    # Every returned point lies inside the disk (radius 15 about the origin).
    assert square
    assert all((p[0] ** 2 + p[1] ** 2) <= 15.0 ** 2 + 1e-6 for p in square)
