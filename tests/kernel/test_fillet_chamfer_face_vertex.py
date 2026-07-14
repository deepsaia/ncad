import pytest

pytestmark = pytest.mark.slow


def test_fillet_face_rounds_all_bounding_edges():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    face = box.faces()[0]
    result = kernel.fillet_face(box, [face], 2.0)
    # Rounding a face's four edges removes material (less than the plain box).
    assert result.volume < box.volume


def test_vertex_chamfer_facets_a_corner():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    vertex = box.vertices()[0]
    result = kernel.chamfer_vertices(box, [vertex], 2.0)
    assert result.volume < box.volume
    # A corner facet adds a new triangular face (the box's 6 faces plus the facet).
    assert len(result.faces()) > 6
