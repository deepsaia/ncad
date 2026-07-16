import math

import pytest

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.motion_driver import MotionParamError
from ncad.assembly.motion_pins import driver_pins


def _rev_frames():
    # ground pivot + crank hub coaxial about Z at origin, radius 10.
    a = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    b = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    return a, b


def test_revolute_driver_pins_witness_and_target_at_radius():
    a, b = _rev_frames()
    prims = driver_pins("revolute", 90.0,
                        {"instance": "base", "connector": "pivot"},
                        {"instance": "arm", "connector": "hub"}, a, b)
    drive = next(p for p in prims if p["kind"] == "drive_to_point")
    # the moving side is the crank hub (the joint's b_ref, the placed body), reference is the base.
    assert drive["a_ref"] == {"instance": "arm", "connector": "hub"}
    assert drive["b_ref"] == {"instance": "base", "connector": "pivot"}
    # witness rides the moving connector's local +X at the radius: (10, 0, 0).
    assert math.isclose(drive["witness"][0], 10.0, abs_tol=1e-6)
    assert math.isclose(drive["witness"][1], 0.0, abs_tol=1e-6)
    # target at 90deg in the reference frame's x-y plane: (0, 10, 0).
    assert math.isclose(drive["target"][0], 0.0, abs_tol=1e-6)
    assert math.isclose(drive["target"][1], 10.0, abs_tol=1e-6)


def test_slider_driver_pins_distance():
    a = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    b = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    prims = driver_pins("slider", 12.0,
                        {"instance": "g", "connector": "way"},
                        {"instance": "block", "connector": "face"}, a, b)
    pin = next(p for p in prims if p["kind"] == "point_plane_distance")
    assert pin["value"] == 12.0
    assert pin["a_ref"] == {"instance": "block", "connector": "face"}  # the moving body


def test_fixed_joint_is_not_drivable():
    a, b = _rev_frames()
    with pytest.raises(MotionParamError):
        driver_pins("fixed", 10.0, {"instance": "g", "connector": "c"},
                    {"instance": "m", "connector": "c"}, a, b)
