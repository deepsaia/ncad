import math

from ncad.assembly.assembly_placement import AssemblyPlacement


def test_absent_placement_is_identity() -> None:
    m = AssemblyPlacement().matrix(None)
    assert m == [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def test_position_only_translates() -> None:
    m = AssemblyPlacement().matrix({"position": [10, 20, 30]})
    # Row-major: the translation sits in the last row (viewer/three.js convention documented).
    assert m[3][0] == 10 and m[3][1] == 20 and m[3][2] == 30


def test_axis_angle_rotation_about_z() -> None:
    m = AssemblyPlacement().matrix({"rotation": {"axis": [0, 0, 1], "angle": 90}})
    # A 90deg rotation about Z: the top-left 2x2 is a rotation (diagonal ~0, off-diagonal ~+/-1).
    assert math.isclose(m[0][0], 0.0, abs_tol=1e-9)
    assert math.isclose(abs(m[0][1]), 1.0, abs_tol=1e-9)


def test_euler_rotation_runs() -> None:
    m = AssemblyPlacement().matrix({"rotation": {"euler": [0, 0, 90]}})
    assert math.isclose(m[0][0], 0.0, abs_tol=1e-9)
