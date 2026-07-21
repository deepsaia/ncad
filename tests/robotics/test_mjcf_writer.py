"""MjcfWriter emits nested bodies, full inertia, mesh assets, loop equalities, and actuators."""

import xml.etree.ElementTree as ET

from ncad.robotics.mjcf_writer import MjcfWriter
from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel


def _model():
    links = [
        RobotLink("base", mass=2.0, inertia={"ixx": 1.0, "iyy": 1.0, "izz": 1.0},
                  mesh="meshes/b.stl"),
        RobotLink("arm", mass=0.5, inertia={"ixx": 0.1, "iyy": 0.1, "izz": 0.1, "ixy": 0.02},
                  center_of_mass=(0, 0, 0.05), mesh="meshes/a.stl"),
        RobotLink("tool", mass=0.2, inertia={"ixx": 0.01, "iyy": 0.01, "izz": 0.01}),
    ]
    joints = [
        RobotJoint("j1", "revolute", "base", "arm", origin_xyz=(0, 0, 0.1), axis=(0, 0, 1),
                   limit_lower=-1.5, limit_upper=1.5, effort=30.0, damping=0.1),
        RobotJoint("j2", "prismatic", "arm", "tool", axis=(1, 0, 0)),
        RobotJoint("loop", "revolute", "tool", "base", origin_xyz=(0, 0, 0.2),
                   is_loop_closure=True),
    ]
    return RobotModel("robot", "base", links, joints)


def test_bodies_are_nested_from_the_base():
    root = ET.fromstring(MjcfWriter().to_xml(_model()))
    base = root.find("worldbody/body[@name='base']")
    assert base is not None
    # arm nests inside base; tool nests inside arm.
    arm = base.find("body[@name='arm']")
    assert arm is not None
    assert arm.find("body[@name='tool']") is not None


def test_joint_is_inside_child_body_with_type_and_range():
    root = ET.fromstring(MjcfWriter().to_xml(_model()))
    arm = root.find("worldbody/body[@name='base']/body[@name='arm']")
    joint = arm.find("joint")
    assert joint.get("type") == "hinge"       # revolute -> hinge
    assert joint.get("range") == "-1.5 1.5"
    assert joint.get("damping") == "0.1"


def test_full_inertia_tensor_and_mesh_asset():
    root = ET.fromstring(MjcfWriter().to_xml(_model()))
    arm = root.find("worldbody/body[@name='base']/body[@name='arm']")
    inertial = arm.find("inertial")
    # fullinertia carries the off-diagonal ixy the diagonalized form would lose.
    assert "0.02" in inertial.get("fullinertia")
    assert {m.get("name") for m in root.findall("asset/mesh")} == {"base_mesh", "arm_mesh"}


def test_loop_closure_is_an_equality_connect():
    root = ET.fromstring(MjcfWriter().to_xml(_model()))
    connect = root.find("equality/connect")
    assert connect is not None
    assert {connect.get("body1"), connect.get("body2")} == {"tool", "base"}


def test_actuated_joint_gets_an_actuator():
    root = ET.fromstring(MjcfWriter().to_xml(_model()))
    actuators = root.findall("actuator/position")
    assert [a.get("joint") for a in actuators] == ["j1"]   # only the joint with authored effort
