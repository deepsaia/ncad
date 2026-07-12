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


def test_revolute_value_leaves_rotation_free() -> None:
    # Rotation-pinning (a revolute angle) is deferred to Phase 6 forward kinematics: an angular
    # value does not pin a static solve, so the joint lowers to its positioning primitives only.
    kinds = _kinds({"id": "j", "type": "revolute", "value": 30})
    assert kinds == ["axes_coincident", "point_in_plane"]


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


def test_screw_valueless_positioning_and_signature() -> None:
    prims, sig = JointLowering().lower({"id": "j", "type": "screw", "pitch": 2}, _f(), _f())
    assert [p["kind"] for p in prims] == ["axes_coincident"]
    assert len(sig) == 1 and sig[0].motion == "screw" and sig[0].pitch == 2.0


def test_screw_valued_pins_axial_depth_only() -> None:
    # A screw's value is the turn angle; its coupled axial travel (theta/360 * pitch) pins the
    # DEPTH (solves statically). The rotation pin is deferred to Phase 6, so only the axial pin
    # is added alongside the coaxial positioning.
    prims, _ = JointLowering().lower(
        {"id": "j", "type": "screw", "pitch": 2, "value": 360}, _f(), _f())
    kinds = [p["kind"] for p in prims]
    assert kinds == ["axes_coincident", "point_plane_distance"]
    # One full turn (360 deg) advances by exactly one pitch (2mm).
    axial = next(p for p in prims if p["kind"] == "point_plane_distance")
    assert axial["value"] == 2.0


def test_valued_screw_without_pitch_raises() -> None:
    with pytest.raises(JointError):
        JointLowering().lower({"id": "j", "type": "screw", "value": 90}, _f(), _f())
