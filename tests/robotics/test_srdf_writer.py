"""SrdfWriter: emit SRDF XML (planning groups, end-effectors, group states, adjacency pairs)."""

import xml.etree.ElementTree as ET
from pathlib import Path

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel
from ncad.robotics.srdf_spec import SrdfSpec
from ncad.robotics.srdf_writer import SrdfWriter
from ncad.spec.spec_loader import SpecLoader

_GOLDEN = Path(__file__).parent / "goldens" / "desk_arm.srdf"
_EXAMPLE = "examples/08-robotics/desk_arm.physics.hocon"


def _model() -> RobotModel:
    links = [RobotLink(name=n, mass=1.0)
             for n in ("base", "turret", "upperarm", "forearm", "hand", "jaw")]
    joints = [
        RobotJoint(name="base_yaw", joint_type="revolute", parent="base", child="turret"),
        RobotJoint(name="shoulder", joint_type="revolute", parent="turret", child="upperarm"),
        RobotJoint(name="elbow", joint_type="revolute", parent="upperarm", child="forearm"),
        RobotJoint(name="wrist", joint_type="revolute", parent="forearm", child="hand"),
        RobotJoint(name="grip", joint_type="prismatic", parent="hand", child="jaw"),
    ]
    return RobotModel(name="desk_arm", base_link="base", links=links, joints=joints)


def test_emits_wellformed_robot_with_chain_group():
    doc = {"physics": {"srdf": {"groups": [{"name": "arm", "base": "base", "tip": "hand"}]}}}
    xml = SrdfWriter().to_xml(_model(), SrdfSpec(doc, _model()))
    root = ET.fromstring(xml)
    assert root.tag == "robot"
    assert root.attrib["name"] == "desk_arm"
    arm = next(g for g in root.findall("group") if g.attrib["name"] == "arm")
    chain = arm.find("chain")
    assert chain is not None
    assert chain.attrib["base_link"] == "base"
    assert chain.attrib["tip_link"] == "hand"


def test_joint_list_group_emits_joint_elements():
    doc = {"physics": {"srdf": {"groups": [{"name": "gripper", "joints": ["grip"]}]}}}
    xml = SrdfWriter().to_xml(_model(), SrdfSpec(doc, _model()))
    root = ET.fromstring(xml)
    gripper = next(g for g in root.findall("group") if g.attrib["name"] == "gripper")
    assert [j.attrib["name"] for j in gripper.findall("joint")] == ["grip"]


def test_derives_adjacency_disable_collisions():
    xml = SrdfWriter().to_xml(_model(), SrdfSpec({"physics": {}}, _model()))
    root = ET.fromstring(xml)
    pairs = {frozenset((d.attrib["link1"], d.attrib["link2"]))
             for d in root.findall("disable_collisions")}
    assert frozenset(("base", "turret")) in pairs
    assert frozenset(("forearm", "hand")) in pairs
    assert frozenset(("hand", "jaw")) in pairs
    # a non-adjacent pair is NOT disabled
    assert frozenset(("base", "jaw")) not in pairs


def test_emits_end_effector_and_group_state():
    doc = {"physics": {"srdf": {
        "groups": [{"name": "arm", "base": "base", "tip": "hand"},
                   {"name": "gripper", "joints": ["grip"]}],
        "end_effectors": [{"name": "hand_ee", "parent": "hand", "group": "gripper"}],
        "group_states": [{"name": "home", "group": "arm",
                          "values": {"base_yaw": 0, "shoulder": 0, "elbow": 0, "wrist": 0}}],
    }}}
    root = ET.fromstring(SrdfWriter().to_xml(_model(), SrdfSpec(doc, _model())))
    ee = root.find("end_effector")
    assert ee is not None
    assert ee.attrib["name"] == "hand_ee"
    assert ee.attrib["parent_link"] == "hand"
    assert ee.attrib["group"] == "gripper"
    state = root.find("group_state")
    assert state is not None
    assert state.attrib["name"] == "home" and state.attrib["group"] == "arm"
    assert {j.attrib["name"] for j in state.findall("joint")} == {
        "base_yaw", "shoulder", "elbow", "wrist"}


def test_pure_same_inputs_same_xml():
    doc = {"physics": {}}
    first = SrdfWriter().to_xml(_model(), SrdfSpec(doc, _model()))
    second = SrdfWriter().to_xml(_model(), SrdfSpec(doc, _model()))
    assert first == second


def test_desk_arm_authored_srdf_matches_golden():
    """The srdf {} block authored in the desk_arm example emits the checked-in golden SRDF.

    Uses a fixture model matching desk_arm's topology (no kernel build needed), so a change to the
    example's srdf block or the writer output is caught here fast.
    """
    document = SpecLoader().load(_EXAMPLE)
    xml = SrdfWriter().to_xml(_model(), SrdfSpec(document, _model()))
    assert xml == _GOLDEN.read_text(encoding="utf-8")
