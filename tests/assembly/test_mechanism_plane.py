import math

from ncad.assembly.mechanism_plane import MechanismPlane


def test_to_2d_projects_onto_plane_axes():
    plane = MechanismPlane.from_axis_point((0, 0, 0), (0, 0, 1))  # XY plane, e1~+X e2~+Y
    u, v = plane.to_2d((3.0, 4.0, 9.0))
    assert math.isclose(u, 3.0, abs_tol=1e-9)
    assert math.isclose(v, 4.0, abs_tol=1e-9)


def test_delta_matrix_pure_translation():
    plane = MechanismPlane.from_axis_point((0, 0, 0), (0, 0, 1))
    m = plane.delta_matrix(0.0, 5.0, -2.0)
    p = _apply((1.0, 1.0, 0.0), m)
    assert math.isclose(p[0], 6.0, abs_tol=1e-9)
    assert math.isclose(p[1], -1.0, abs_tol=1e-9)


def test_delta_matrix_rotation_about_normal():
    plane = MechanismPlane.from_axis_point((0, 0, 0), (0, 0, 1))
    m = plane.delta_matrix(math.pi / 2, 0.0, 0.0)  # +90deg about +Z: (1,0)->(0,1)
    p = _apply((1.0, 0.0, 0.0), m)
    assert math.isclose(p[0], 0.0, abs_tol=1e-9)
    assert math.isclose(p[1], 1.0, abs_tol=1e-9)


def test_delta_matrix_on_offset_plane_in_xz():
    # Plane normal +Y through (0,10,0): a mechanism in the X-Z plane. Rotation stays in-plane.
    plane = MechanismPlane.from_axis_point((0, 10, 0), (0, 1, 0))
    m = plane.delta_matrix(math.pi / 2, 0.0, 0.0)
    # a point in the plane keeps its Y (in-plane rotation does not move it off-plane).
    p = _apply((1.0, 10.0, 0.0), m)
    assert math.isclose(p[1], 10.0, abs_tol=1e-9)


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))
