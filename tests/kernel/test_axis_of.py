import math

import pytest

pytestmark = pytest.mark.slow


def test_axis_of_fillet_cylinder_matches_expected() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = kernel.extrude(kernel.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"), 20.0)
    filleted = kernel.fillet_edges(box, [kernel.edges_of(box)[0]["edge"]], 4.0)
    cyl = next(f for f in filleted.faces() if f.geom_type.name == "CYLINDER")
    axis = kernel.axis_of(cyl)
    assert axis is not None
    assert math.isclose(axis["radius"], 4.0, abs_tol=1e-6)
    # A vertical fillet on a Z-extruded box has a Z-ish axis direction.
    assert abs(axis["direction"][2]) > 0.9


def test_axis_of_planar_face_is_none() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 10.0)
    planar = next(f for f in box.faces() if f.geom_type.name == "PLANE")
    assert kernel.axis_of(planar) is None
