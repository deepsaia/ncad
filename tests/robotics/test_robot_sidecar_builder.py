"""RobotSidecarBuilder: tree fields, actuated detection, sweep range rules (unit + slow build)."""

import json

import pytest

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel
from ncad.robotics.robot_sidecar_builder import RobotSidecarBuilder


def _model():
    links = [
        RobotLink("base", mass=2.0, inertia={"ixx": 1.0, "iyy": 1.0, "izz": 1.0}),
        RobotLink("arm", mass=0.5, inertia={"ixx": 0.1, "iyy": 0.1, "izz": 0.1},
                  center_of_mass=(0.0, 0.0, 0.05), mesh="meshes/arm.stl"),
    ]
    joints = [
        RobotJoint("j1", "revolute", "base", "arm", axis=(0, 0, 1),
                   limit_lower=-1.5, limit_upper=1.5),
        RobotJoint("j2", "continuous", "arm", "base", is_loop_closure=True),
    ]
    return RobotModel("robot", "base", links, joints)


def test_tree_carries_links_joints_and_actuated_flag():
    builder = RobotSidecarBuilder(kernel=None)
    tree = builder._tree(_model(), actuated={"j1"})
    assert tree["base_link"] == "base"
    assert [link["name"] for link in tree["links"]] == ["base", "arm"]
    j1 = next(j for j in tree["joints"] if j["name"] == "j1")
    assert j1["actuated"] is True and j1["limit"] == [-1.5, 1.5]
    j2 = next(j for j in tree["joints"] if j["name"] == "j2")
    assert j2["actuated"] is False and j2["loop_closure"] is True
    # the arm link carries its computed inertia + mesh for the inspector.
    arm = next(link for link in tree["links"] if link["name"] == "arm")
    assert arm["mesh"] == "meshes/arm.stl" and arm["inertia"]["ixx"] == 0.1


def test_range_uses_authored_limits():
    builder = RobotSidecarBuilder(kernel=None)
    joint = RobotJoint("j", "revolute", "a", "b", limit_lower=-2.0, limit_upper=2.0)
    assert builder._range(joint, model_size=1.0) == (-2.0, 2.0)


def test_range_full_turn_for_unlimited_revolute():
    import math
    builder = RobotSidecarBuilder(kernel=None)
    joint = RobotJoint("j", "continuous", "a", "b")
    low, high = builder._range(joint, model_size=1.0)
    assert low == 0.0 and high == pytest.approx(2.0 * math.pi)


def test_range_auto_travel_for_unlimited_prismatic():
    builder = RobotSidecarBuilder(kernel=None)
    joint = RobotJoint("j", "prismatic", "a", "b")
    low, high = builder._range(joint, model_size=0.4)
    assert low == 0.0 and high == pytest.approx(0.2)   # 0.5 * model_size


@pytest.mark.slow
def test_build_writes_tree_and_sweep_sidecars(tmp_path):
    from ncad.kernel.build123d_kernel import Build123dKernel

    RobotSidecarBuilder(Build123dKernel()).build(
        "examples/08-robotics/crank_slider.physics.hocon", str(tmp_path), with_sweeps=True)
    tree = json.loads((tmp_path / "crank_slider.robot.json").read_text())
    assert tree["base_link"] == "block"
    assert {link["name"] for link in tree["links"]} == {"block", "flywheel", "rod", "piston"}

    sweeps = json.loads((tmp_path / "crank_slider.robot_sweeps.json").read_text())
    # mainPin is the only actuated joint; its sweep drives the closed loop across the limit.
    assert "mainPin" in sweeps
    frames = sweeps["mainPin"]["frames"]
    assert len(frames) > 1
    # The sweep must actually articulate the FULL range, not a few degrees: mainPin's URDF limit is
    # [-pi, pi] rad (a full turn), so the flywheel must rotate ~360 degrees. The bug was feeding
    # those radian limits to the motion driver (which reads revolute values in DEGREES), rotating
    # the crank ~6 degrees. R[0][0] = cos(rotation) must reach both extremes (~-1 and ~+1).
    cos_rot = [f["placements"]["flywheel"][0][0] for f in frames]
    assert min(cos_rot) < -0.9 and max(cos_rot) > 0.9, "sweep did not articulate the full turn"
    # the per-joint solve was isolated: no stray .motion.json churned into the output dir.
    assert not (tmp_path / "crank_slider.motion.json").exists()


@pytest.mark.slow
def test_sweeps_are_opt_in(tmp_path):
    # Default (with_sweeps False): the cheap tree writes, but NOT the expensive sweep sidecar.
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = RobotSidecarBuilder(Build123dKernel()).build(
        "examples/08-robotics/crank_slider.physics.hocon", str(tmp_path), with_sweeps=False)
    assert (tmp_path / "crank_slider.robot.json").is_file()
    assert result["sweeps"] is None
    assert not (tmp_path / "crank_slider.robot_sweeps.json").exists()
