"""SrdfSpec: parse + validate the physics ``srdf {}`` overlay block against a RobotModel."""

import pytest

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel
from ncad.robotics.srdf_spec import SrdfSpec, SrdfSpecError


def _model() -> RobotModel:
    """A desk-arm-shaped chain: base -> turret -> upperarm -> forearm -> hand -> jaw."""
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


def test_absent_block_synthesizes_default_chain_group():
    spec = SrdfSpec({"physics": {}}, _model())
    assert len(spec.groups) == 1
    group = spec.groups[0]
    # Default chain spans base_link to the deepest leaf link (jaw).
    assert group["base"] == "base"
    assert group["tip"] == "jaw"


def test_chain_joints_walks_tree_between_links():
    spec = SrdfSpec({"physics": {}}, _model())
    assert spec.chain_joints("base", "hand") == ["base_yaw", "shoulder", "elbow", "wrist"]


def test_authored_groups_parsed():
    doc = {"physics": {"srdf": {"groups": [
        {"name": "arm", "base": "base", "tip": "hand"},
        {"name": "gripper", "joints": ["grip"]},
    ]}}}
    spec = SrdfSpec(doc, _model())
    assert {g["name"] for g in spec.groups} == {"arm", "gripper"}


def test_end_effectors_and_group_states_parsed():
    doc = {"physics": {"srdf": {
        "groups": [{"name": "arm", "base": "base", "tip": "hand"},
                   {"name": "gripper", "joints": ["grip"]}],
        "end_effectors": [{"name": "hand_ee", "parent": "hand", "group": "gripper"}],
        "group_states": [{"name": "home", "group": "arm",
                          "values": {"base_yaw": 0, "shoulder": 0, "elbow": 0, "wrist": 0}}],
    }}}
    spec = SrdfSpec(doc, _model())
    assert spec.end_effectors[0]["name"] == "hand_ee"
    assert spec.group_states[0]["group"] == "arm"


def test_group_with_unknown_tip_raises():
    doc = {"physics": {"srdf": {"groups": [{"name": "arm", "base": "base", "tip": "nope"}]}}}
    with pytest.raises(SrdfSpecError):
        SrdfSpec(doc, _model())


def test_group_with_unknown_joint_raises():
    doc = {"physics": {"srdf": {"groups": [{"name": "gripper", "joints": ["ghost"]}]}}}
    with pytest.raises(SrdfSpecError):
        SrdfSpec(doc, _model())


def test_end_effector_unknown_group_raises():
    doc = {"physics": {"srdf": {
        "groups": [{"name": "arm", "base": "base", "tip": "hand"}],
        "end_effectors": [{"name": "ee", "parent": "hand", "group": "ghost"}],
    }}}
    with pytest.raises(SrdfSpecError):
        SrdfSpec(doc, _model())


def test_group_state_joint_not_in_group_raises():
    doc = {"physics": {"srdf": {
        "groups": [{"name": "gripper", "joints": ["grip"]}],
        "group_states": [{"name": "bad", "group": "gripper", "values": {"base_yaw": 0}}],
    }}}
    with pytest.raises(SrdfSpecError):
        SrdfSpec(doc, _model())


def test_chain_joints_no_path_raises():
    spec = SrdfSpec({"physics": {}}, _model())
    with pytest.raises(SrdfSpecError):
        spec.chain_joints("hand", "base")  # wrong direction: no parent->child path
