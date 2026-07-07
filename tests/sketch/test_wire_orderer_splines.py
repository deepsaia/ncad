from ncad.sketch.wire_orderer import WireOrderer


def test_bezier_in_closed_loop_emits_descriptor():
    entities = [
        {"id": "bz", "type": "bezier", "points": ["p0", "p1", "p2", "p3"]},
        {"id": "l1", "type": "line", "p1": "p3", "p2": "q1"},
        {"id": "l2", "type": "line", "p1": "q1", "p2": "q2"},
        {"id": "l3", "type": "line", "p1": "q2", "p2": "p0"},
    ]
    pos = {"p0": (0.0, 0.0), "p1": (1.0, 2.0), "p2": (3.0, 2.0), "p3": (4.0, 0.0),
           "q1": (4.0, -1.0), "q2": (0.0, -1.0)}
    edges, err = WireOrderer().order(entities, pos, {})
    assert err is None
    bez = [e for e in edges if e["kind"] == "bezier"]
    assert len(bez) == 1
    assert len(bez[0]["points"]) == 4


def test_interpolated_emits_spline_kind():
    entities = [
        {"id": "sp", "type": "interpolated", "points": ["p0", "p1", "p3"]},
        {"id": "l1", "type": "line", "p1": "p3", "p2": "q2"},
        {"id": "l2", "type": "line", "p1": "q2", "p2": "p0"},
    ]
    pos = {"p0": (0.0, 0.0), "p1": (2.0, 3.0), "p3": (4.0, 0.0), "q2": (0.0, -1.0)}
    edges, err = WireOrderer().order(entities, pos, {})
    assert err is None
    assert any(e["kind"] == "spline" for e in edges)


def test_spline_in_open_path():
    entities = [
        {"id": "bz", "type": "bezier", "points": ["p0", "p1", "p2", "p3"]},
        {"id": "l1", "type": "line", "p1": "p3", "p2": "q1"},
    ]
    pos = {"p0": (0.0, 0.0), "p1": (1.0, 2.0), "p2": (3.0, 2.0), "p3": (4.0, 0.0),
           "q1": (6.0, 0.0)}
    edges, err = WireOrderer().order_open(entities, pos, {})
    assert err is None
    assert edges[0]["kind"] == "bezier"
    assert edges[0]["points"][0] == (0.0, 0.0)
    assert edges[0]["points"][-1] == (4.0, 0.0)


def test_spline_reversed_when_traversed_end_to_start():
    # Open path authored so the walk enters the bezier from its LAST point (p3):
    # line q1->p3, then bezier. The emitted bezier point list must be reversed so it
    # starts at p3 and ends at p0, matching path direction.
    entities = [
        {"id": "l1", "type": "line", "p1": "q1", "p2": "p3"},
        {"id": "bz", "type": "bezier", "points": ["p0", "p1", "p2", "p3"]},
    ]
    pos = {"q1": (-2.0, 0.0), "p0": (0.0, 0.0), "p1": (1.0, 2.0),
           "p2": (3.0, 2.0), "p3": (4.0, 0.0)}
    edges, err = WireOrderer().order_open(entities, pos, {})
    assert err is None
    bez = [e for e in edges if e["kind"] == "bezier"][0]
    assert bez["points"][0] == (4.0, 0.0)
    assert bez["points"][-1] == (0.0, 0.0)
