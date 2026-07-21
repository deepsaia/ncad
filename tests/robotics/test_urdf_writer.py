"""UrdfWriter emits valid URDF: links with inertials, type-mapped joints, tree-only."""

import xml.etree.ElementTree as ET

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel
from ncad.robotics.urdf_writer import UrdfWriter


def _model():
    links = [
        RobotLink("base", mass=2.0, inertia={"ixx": 1.0, "iyy": 1.0, "izz": 1.0}),
        RobotLink("arm", mass=0.5, inertia={"ixx": 0.1, "iyy": 0.1, "izz": 0.1},
                  center_of_mass=(0.0, 0.0, 0.05), mesh="meshes/arm.stl"),
        RobotLink("tool", mass=0.2, inertia={"ixx": 0.01, "iyy": 0.01, "izz": 0.01}),
    ]
    joints = [
        RobotJoint("j1", "revolute", "base", "arm", origin_xyz=(0, 0, 0.1), axis=(0, 0, 1),
                   limit_lower=-1.5, limit_upper=1.5, effort=30.0, velocity=2.0, damping=0.1),
        RobotJoint("j2", "continuous", "arm", "tool", axis=(1, 0, 0)),
        RobotJoint("loop", "revolute", "tool", "base", is_loop_closure=True),
    ]
    return RobotModel("robot", "base", links, joints)


def test_urdf_has_all_links_and_tree_joints_only():
    root = ET.fromstring(UrdfWriter().to_xml(_model()))
    assert root.tag == "robot" and root.get("name") == "robot"
    assert {link.get("name") for link in root.findall("link")} == {"base", "arm", "tool"}
    # The loop-closure joint is excluded; only the two tree joints are emitted.
    assert {j.get("name") for j in root.findall("joint")} == {"j1", "j2"}


def test_revolute_joint_has_limit_and_dynamics():
    root = ET.fromstring(UrdfWriter().to_xml(_model()))
    j1 = next(j for j in root.findall("joint") if j.get("name") == "j1")
    assert j1.get("type") == "revolute"
    limit = j1.find("limit")
    assert limit.get("lower") == "-1.5" and limit.get("upper") == "1.5"
    assert limit.get("effort") == "30" and limit.get("velocity") == "2"
    assert j1.find("dynamics").get("damping") == "0.1"


def test_continuous_joint_omits_limit_bounds():
    root = ET.fromstring(UrdfWriter().to_xml(_model()))
    j2 = next(j for j in root.findall("joint") if j.get("name") == "j2")
    assert j2.get("type") == "continuous"
    # No authored effort/velocity and not revolute/prismatic -> no <limit> element at all.
    assert j2.find("limit") is None


def test_link_inertial_and_mesh():
    root = ET.fromstring(UrdfWriter().to_xml(_model()))
    arm = next(link for link in root.findall("link") if link.get("name") == "arm")
    assert arm.find("inertial/mass").get("value") == "0.5"
    assert arm.find("inertial/origin").get("xyz") == "0 0 0.05"
    assert arm.find("visual/geometry/mesh").get("filename") == "meshes/arm.stl"
    # An inertia-only link (no mesh) has no visual/collision.
    base = next(link for link in root.findall("link") if link.get("name") == "base")
    assert base.find("visual") is None
