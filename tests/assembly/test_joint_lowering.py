import pytest

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.joint_lowering import JointError, JointLowering


def _f() -> ConnectorFrame:
    return ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))


def _kinds(joint) -> list[str]:
    prims, _ = JointLowering().lower(joint, _f(), _f())
    return [p["kind"] for p in prims]


def test_fixed_lowers_to_full_lock() -> None:
    assert _kinds({"id": "j", "type": "fixed"}) == [
        "points_coincident", "anti_parallel_dirs", "secondary_parallel"]


def test_revolute_valueless() -> None:
    prims, sig = JointLowering().lower({"id": "j", "type": "revolute"}, _f(), _f())
    assert [p["kind"] for p in prims] == ["axes_coincident", "point_in_plane"]
    assert [a.motion for a in sig] == ["rotation"]


def test_revolute_value_adds_angle_pin() -> None:
    kinds = _kinds({"id": "j", "type": "revolute", "value": 30})
    assert kinds == ["axes_coincident", "point_in_plane", "dirs_angle"]


def test_slider_blocks_spin() -> None:
    assert _kinds({"id": "j", "type": "slider"}) == ["axes_coincident", "secondary_parallel"]


def test_slider_value_adds_distance() -> None:
    assert _kinds({"id": "j", "type": "slider", "value": 5}) == [
        "axes_coincident", "secondary_parallel", "point_plane_distance"]


def test_cylindrical_is_axes_only() -> None:
    assert _kinds({"id": "j", "type": "cylindrical"}) == ["axes_coincident"]


def test_planar_lowering() -> None:
    assert _kinds({"id": "j", "type": "planar"}) == ["point_in_plane", "parallel_dirs"]


def test_ball_is_points_coincident() -> None:
    assert _kinds({"id": "j", "type": "ball"}) == ["points_coincident"]


def test_point_on_line() -> None:
    prims, sig = JointLowering().lower({"id": "j", "type": "point_on_line"}, _f(), _f())
    assert [p["kind"] for p in prims] == ["point_on_line"]
    assert sig[0].axis == "line"


def test_signature_returned_for_ball() -> None:
    _, sig = JointLowering().lower({"id": "j", "type": "ball"}, _f(), _f())
    assert [a.motion for a in sig] == ["rotation", "rotation", "rotation"]


def test_unknown_type_raises() -> None:
    with pytest.raises(JointError):
        JointLowering().lower({"id": "j", "type": "warp"}, _f(), _f())
