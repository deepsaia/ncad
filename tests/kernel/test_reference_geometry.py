import pytest

pytestmark = pytest.mark.slow


def test_project_vertices_onto_plane():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    box = Solid.make_box(10, 10, 10)
    verts = list(box.vertices())
    pts = Build123dKernel().project_vertices(verts[:2], "XY")
    assert len(pts) == 2
    assert all(len(p) == 2 for p in pts)


def test_intersection_curve_of_box_and_plane():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    box = Solid.make_box(10, 10, 10)
    # A plane cutting through the middle yields a closed rectangle of section edges.
    edges = Build123dKernel().intersection_curve(box, "XY", offset=5.0)
    assert len(edges) >= 4
    assert all("kind" in e for e in edges)
