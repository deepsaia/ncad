import math

from ncad.assembly.connector_frame import ConnectorFrame


def _is_unit(v) -> bool:
    return math.isclose(math.sqrt(sum(c * c for c in v)), 1.0, abs_tol=1e-9)


def _orthonormal(f: ConnectorFrame) -> bool:
    def dot(a, b):
        return sum(p * q for p, q in zip(a, b))
    return (_is_unit(f.x) and _is_unit(f.y) and _is_unit(f.z)
            and abs(dot(f.x, f.y)) < 1e-9 and abs(dot(f.y, f.z)) < 1e-9
            and abs(dot(f.x, f.z)) < 1e-9)


def test_planar_frame_z_is_normal_and_orthonormal() -> None:
    f = ConnectorFrame.from_planar((1, 2, 3), (0, 0, 1))
    assert f.origin == (1, 2, 3)
    assert f.z == (0.0, 0.0, 1.0)
    assert _orthonormal(f)


def test_axis_frame_z_is_direction() -> None:
    f = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 2))  # unnormalized direction
    assert f.z == (0.0, 0.0, 1.0)
    assert _orthonormal(f)


def test_offset_shifts_origin_along_axes() -> None:
    # +Z-normal frame at origin, offset 5 along Z -> origin lifts to z=5.
    f = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1), offset=[0, 0, 5])
    assert math.isclose(f.origin[2], 5.0, abs_tol=1e-9)
