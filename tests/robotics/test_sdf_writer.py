"""SdfWriter emits a flat model: links with inertials + every joint (loop closures kept)."""

import xml.etree.ElementTree as ET

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel


def _model():
    links = [
        RobotLink("base", mass=2.0, inertia={"ixx": 1.0, "iyy": 1.0, "izz": 1.0}),
        RobotLink("arm", mass=0.5, inertia={"ixx": 0.1, "iyy": 0.1, "izz": 0.1},
                  mesh="meshes/a.stl"),
    ]
    joints = [
        RobotJoint("j1", "revolute", "base", "arm", origin_xyz=(0, 0, 0.1), axis=(0, 0, 1),
                   limit_lower=-1.0, limit_upper=1.0, effort=20.0, velocity=3.0),
        RobotJoint("loop", "revolute", "arm", "base", is_loop_closure=True),
    ]
    return RobotModel("robot", "base", links, joints)


def _root():
    from ncad.robotics.sdf_writer import SdfWriter
    return ET.fromstring(SdfWriter().to_xml(_model()))


def test_flat_model_with_links_and_all_joints():
    model = _root().find("model")
    assert model.get("name") == "robot"
    assert {link.get("name") for link in model.findall("link")} == {"base", "arm"}
    # SDF is not tree-limited: BOTH joints (incl. the loop closure) are emitted.
    assert {j.get("name") for j in model.findall("joint")} == {"j1", "loop"}


def test_link_inertial_and_mesh_uri():
    model = _root().find("model")
    arm = next(link for link in model.findall("link") if link.get("name") == "arm")
    assert arm.find("inertial/mass").text == "0.5"
    assert arm.find("visual/geometry/mesh/uri").text == "meshes/a.stl"


def test_revolute_joint_axis_and_limit():
    model = _root().find("model")
    j1 = next(j for j in model.findall("joint") if j.get("name") == "j1")
    assert j1.get("type") == "revolute"
    assert j1.find("parent").text == "base" and j1.find("child").text == "arm"
    limit = j1.find("axis/limit")
    assert limit.find("lower").text == "-1" and limit.find("upper").text == "1"
    assert limit.find("effort").text == "20"
