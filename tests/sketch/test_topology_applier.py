import pytest

from ncad.sketch.topology_applier import TopologyApplier, TopologyError


def _crossing_lines():
    # line a is horizontal from (-5,0) to (5,0); tool b is vertical through x=2
    return [
        {"id": "a0", "type": "point", "at": [-5.0, 0.0]},
        {"id": "a1", "type": "point", "at": [5.0, 0.0]},
        {"id": "b0", "type": "point", "at": [2.0, -5.0]},
        {"id": "b1", "type": "point", "at": [2.0, 5.0]},
        {"id": "la", "type": "line", "p1": "a0", "p2": "a1"},
        {"id": "lb", "type": "line", "p1": "b0", "p2": "b1"},
    ]


def test_absent_modify_is_noop():
    ents = _crossing_lines()
    assert TopologyApplier().apply(ents, []) == ents


def test_trim_keeps_named_side():
    # keep the a0 (left) side: la's a1 endpoint moves to the intersection (2,0)
    out = TopologyApplier().apply(_crossing_lines(), [
        {"id": "t", "op": "trim", "of": "la", "at": "lb", "keep": "a0"}])
    moved = [e for e in out if e["type"] == "point" and e["id"] == "t/x"][0]
    assert (round(moved["at"][0], 6), round(moved["at"][1], 6)) == (2.0, 0.0)
    la = [e for e in out if e["id"] == "la"][0]
    # the kept endpoint stays a0; the far endpoint is now t/x
    assert {la["p1"], la["p2"]} == {"a0", "t/x"}
    assert la.get("fixed")


def test_trim_no_intersection_raises():
    parallel = [
        {"id": "a0", "type": "point", "at": [-5.0, 0.0]},
        {"id": "a1", "type": "point", "at": [5.0, 0.0]},
        {"id": "b0", "type": "point", "at": [-5.0, 3.0]},
        {"id": "b1", "type": "point", "at": [5.0, 3.0]},
        {"id": "la", "type": "line", "p1": "a0", "p2": "a1"},
        {"id": "lb", "type": "line", "p1": "b0", "p2": "b1"},
    ]
    with pytest.raises(TopologyError):
        TopologyApplier().apply(parallel, [
            {"id": "t", "op": "trim", "of": "la", "at": "lb", "keep": "a0"}])


def test_extend_moves_nearest_endpoint():
    # la runs (-5,0)->(0,0); tool lb is vertical at x=3; extend la to reach x=3
    ents = [
        {"id": "a0", "type": "point", "at": [-5.0, 0.0]},
        {"id": "a1", "type": "point", "at": [0.0, 0.0]},
        {"id": "b0", "type": "point", "at": [3.0, -5.0]},
        {"id": "b1", "type": "point", "at": [3.0, 5.0]},
        {"id": "la", "type": "line", "p1": "a0", "p2": "a1"},
        {"id": "lb", "type": "line", "p1": "b0", "p2": "b1"},
    ]
    out = TopologyApplier().apply(ents, [
        {"id": "x", "op": "extend", "of": "la", "to": "lb"}])
    moved = [e for e in out if e["type"] == "point" and e["id"] == "x/x"][0]
    assert (round(moved["at"][0], 6), round(moved["at"][1], 6)) == (3.0, 0.0)
    la = [e for e in out if e["id"] == "la"][0]
    # the nearer endpoint (a1 at (0,0)) moved; a0 is untouched
    assert {la["p1"], la["p2"]} == {"a0", "x/x"}


def test_unknown_op_raises():
    with pytest.raises(TopologyError):
        TopologyApplier().apply(_crossing_lines(), [
            {"id": "z", "op": "warp", "of": "la", "at": "lb", "keep": "a0"}])


def test_unknown_entity_raises():
    with pytest.raises(TopologyError):
        TopologyApplier().apply(_crossing_lines(), [
            {"id": "t", "op": "trim", "of": "nope", "at": "lb", "keep": "a0"}])
