import math

from ncad.assembly.body_pose import BodyPose


def test_identity_quaternion_is_translation_only() -> None:
    m = BodyPose().matrix((10.0, 2.0, 0.0), (1.0, 0.0, 0.0, 0.0))
    assert m[0][:3] == [1.0, 0.0, 0.0]
    assert m[1][:3] == [0.0, 1.0, 0.0]
    assert m[2][:3] == [0.0, 0.0, 1.0]
    assert m[3][:3] == [10.0, 2.0, 0.0]


def test_90deg_about_z_rotates_x_to_y() -> None:
    # Quaternion for +90 deg about Z: (cos45, 0, 0, sin45).
    c = math.cos(math.pi / 4)
    m = BodyPose().matrix((0.0, 0.0, 0.0), (c, 0.0, 0.0, c))
    # Row-major point-times-matrix: local +X (1,0,0) maps to +Y.
    px = [1 * m[0][i] + 0 * m[1][i] + 0 * m[2][i] + m[3][i] for i in range(3)]
    assert math.isclose(px[0], 0.0, abs_tol=1e-9)
    assert math.isclose(px[1], 1.0, abs_tol=1e-9)
