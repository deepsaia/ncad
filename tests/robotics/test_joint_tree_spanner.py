"""JointTreeSpanner orients joints into a base-rooted tree and flags loop closures."""

from ncad.robotics.joint_tree_spanner import JointTreeSpanner


def _joint(jid, a, b):
    return {"id": jid, "type": "revolute", "between": [{"instance": a}, {"instance": b}]}


def test_open_chain_all_tree_no_loops():
    joints = [_joint("j1", "base", "l1"), _joint("j2", "l1", "l2")]
    result = JointTreeSpanner().span("base", joints)
    assert result["loop_closures"] == []
    oriented = {(o["parent"], o["child"]) for o in result["oriented"]}
    assert oriented == {("base", "l1"), ("l1", "l2")}


def test_closed_loop_flags_one_closure():
    # A four-body closed loop (crank-slider shape): 4 joints, exactly one closes the loop.
    joints = [
        _joint("mainPin", "block", "flywheel"),
        _joint("crankPin", "flywheel", "rod"),
        _joint("wristPin", "rod", "piston"),
        _joint("slide", "block", "piston"),
    ]
    result = JointTreeSpanner().span("block", joints)
    assert len(result["loop_closures"]) == 1
    assert len(result["oriented"]) == 3
    assert result["reached"] == {"block", "flywheel", "rod", "piston"}


def test_orientation_is_away_from_base_regardless_of_authored_order():
    # Authored child->parent; the spanner still orients base->child.
    joints = [_joint("j1", "l1", "base")]
    result = JointTreeSpanner().span("base", joints)
    assert result["oriented"][0]["parent"] == "base"
    assert result["oriented"][0]["child"] == "l1"


def test_disconnected_component_is_a_loop_closure():
    # l2<->l3 is not reachable from base: reported as a loop closure (not in the base tree).
    joints = [_joint("j1", "base", "l1"), _joint("orphan", "l2", "l3")]
    result = JointTreeSpanner().span("base", joints)
    assert "orphan" in result["loop_closures"]
