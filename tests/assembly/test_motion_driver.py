import pytest

from ncad.assembly.motion_driver import MotionDriver, MotionParamError


def test_parse_even_sweep_inclusive_endpoints():
    joint, values = MotionDriver().parse({"driver": {"joint": "crank", "from": 0, "to": 360,
                                                     "steps": 4}})
    assert joint == "crank"
    assert values == [0.0, 90.0, 180.0, 270.0, 360.0]  # steps=4 -> 5 inclusive frames


def test_parse_negative_range():
    _joint, values = MotionDriver().parse({"driver": {"joint": "s", "from": 10, "to": 0,
                                                      "steps": 2}})
    assert values == [10.0, 5.0, 0.0]


def test_steps_zero_raises():
    with pytest.raises(MotionParamError):
        MotionDriver().parse({"driver": {"joint": "c", "from": 0, "to": 90, "steps": 0}})


def test_from_equals_to_raises():
    with pytest.raises(MotionParamError):
        MotionDriver().parse({"driver": {"joint": "c", "from": 5, "to": 5, "steps": 3}})


def test_missing_driver_or_joint_raises():
    with pytest.raises(MotionParamError):
        MotionDriver().parse({})
    with pytest.raises(MotionParamError):
        MotionDriver().parse({"driver": {"from": 0, "to": 90, "steps": 3}})
