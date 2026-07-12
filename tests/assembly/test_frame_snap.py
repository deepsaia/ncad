import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.frame_snap import FrameSnap


def _apply(m, p):
    # Row-major with translation in the last row: p' = p . R + t.
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))


def test_snap_maps_moving_origin_onto_target() -> None:
    moving = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    target = ConnectorFrame.from_planar((10, 5, 2), (0, 0, 1))
    m = FrameSnap().transform(moving, target)
    got = _apply(m, moving.origin)
    assert all(math.isclose(got[i], target.origin[i], abs_tol=1e-6) for i in range(3))


def test_identity_when_frames_coincide() -> None:
    f = ConnectorFrame.from_planar((1, 2, 3), (0, 0, 1))
    m = FrameSnap().transform(f, f)
    got = _apply(m, (1, 2, 3))
    assert all(math.isclose(got[i], (1, 2, 3)[i], abs_tol=1e-6) for i in range(3))


def test_offset_gaps_along_target_z() -> None:
    moving = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    target = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    m = FrameSnap().transform(moving, target, offset=4.0)
    got = _apply(m, (0, 0, 0))
    assert math.isclose(got[2], 4.0, abs_tol=1e-6)
