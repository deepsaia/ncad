import pytest

from ncad.build.rebuild_graph import GraphCycleError, RebuildGraph


def _features():
    return [
        {"id": "sk", "op": "sketch"},
        {"id": "pad", "op": "extrude", "profile": "sk"},
        {"id": "hole", "op": "hole", "on": "pad.cap(+Z)"},
        {"id": "rnd", "op": "fillet", "edges": "vertical"},
    ]


def test_order_is_topological():
    graph = RebuildGraph(_features())
    order = graph.order()
    assert order.index("sk") < order.index("pad") < order.index("hole") < order.index("rnd")


def test_extrude_depends_on_its_profile():
    assert RebuildGraph(_features()).deps("pad") == ["sk"]


def test_sketch_has_no_deps():
    assert RebuildGraph(_features()).deps("sk") == []


def test_dressup_depends_on_working_solid_predecessor():
    graph = RebuildGraph(_features())
    assert graph.deps("hole") == ["pad"]
    assert graph.deps("rnd") == ["hole"]


def test_boolean_depends_on_target_and_tool():
    features = [
        {"id": "a", "op": "sketch"},
        {"id": "b", "op": "sketch"},
        {"id": "pa", "op": "extrude", "profile": "a"},
        {"id": "pb", "op": "extrude", "profile": "b"},
        {"id": "bool", "op": "boolean", "target": "pa", "tool": "pb"},
    ]
    assert sorted(RebuildGraph(features).deps("bool")) == ["pa", "pb"]


def test_implicit_input_op_keeps_authored_order_after_its_predecessor():
    # A pattern consumes the authored-previous solid implicitly (no ref). An independent
    # later solid (boss) must NOT be scheduled before the pattern: a feature stack runs in
    # authored order except where an explicit dependency forces something earlier. Otherwise
    # the pattern would replicate the boss instead of the stud (the running-shape it inherits).
    features = [
        {"id": "stud_sk", "op": "sketch"},
        {"id": "stud", "op": "extrude", "profile": "stud_sk"},
        {"id": "row", "op": "pattern"},
        {"id": "boss_sk", "op": "sketch"},
        {"id": "boss", "op": "extrude", "profile": "boss_sk"},
        {"id": "grp", "op": "boolean", "target": "row", "tool": "boss"},
    ]
    order = RebuildGraph(features).order()
    # row must come before boss (authored order preserved for independent solids)
    assert order.index("row") < order.index("boss")
    # and the running-shape chain is stud -> row (not boss -> row)
    assert order.index("stud") < order.index("row")


def test_cycle_raises():
    features = [
        {"id": "x", "op": "extrude", "profile": "y"},
        {"id": "y", "op": "extrude", "profile": "x"},
    ]
    with pytest.raises(GraphCycleError):
        RebuildGraph(features).order()
