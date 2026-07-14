import pytest

pytestmark = pytest.mark.slow


def test_box_inertia_diagonal():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    box = Solid.make_box(10, 20, 30)
    inertia = Build123dKernel().inertia(box)
    m = inertia["matrix"]
    # An axis-aligned box about its centroid: off-diagonals ~0, diagonal all positive.
    assert abs(m[0][1]) < 1e-3 and abs(m[0][2]) < 1e-3 and abs(m[1][2]) < 1e-3
    assert m[0][0] > 0 and m[1][1] > 0 and m[2][2] > 0
    assert len(inertia["principal"]) == 3


def test_inertia_matrix_is_symmetric():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    solid = Solid.make_cylinder(8, 20)
    m = Build123dKernel().inertia(solid)["matrix"]
    assert abs(m[0][1] - m[1][0]) < 1e-6
    assert abs(m[0][2] - m[2][0]) < 1e-6
    assert abs(m[1][2] - m[2][1]) < 1e-6
