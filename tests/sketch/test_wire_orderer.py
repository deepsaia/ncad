import math

from ncad.sketch.wire_orderer import WireOrderer


def test_line_loop_orders_edges():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [10, 0]},
        {"id": "p2", "type": "point", "at": [10, 10]},
        {"id": "p3", "type": "point", "at": [0, 10]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
        {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
        {"id": "l2", "type": "line", "p1": "p2", "p2": "p3"},
        {"id": "l3", "type": "line", "p1": "p3", "p2": "p0"},
    ]
    positions = {"p0": (0, 0), "p1": (10, 0), "p2": (10, 10), "p3": (0, 10)}
    edges, err = WireOrderer().order(entities, positions, {})
    assert err is None
    assert [e["kind"] for e in edges] == ["line", "line", "line", "line"]


def test_single_circle_emits_circle_edge():
    entities = [
        {"id": "cp", "type": "point", "at": [0, 0]},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 5},
    ]
    edges, err = WireOrderer().order(entities, {"cp": (0, 0)}, {"c0": 5.0})
    assert err is None
    assert edges == [{"kind": "circle", "center": (0, 0), "radius": 5.0}]


def test_mixed_line_arc_loop_computes_arc_mid():
    entities = [
        {"id": "cen", "type": "point", "at": [0, 0]},
        {"id": "s", "type": "point", "at": [10, 0]},
        {"id": "e", "type": "point", "at": [0, 10]},
        {"id": "arc", "type": "arc", "center": "cen", "start": "s", "end": "e"},
        {"id": "l0", "type": "line", "p1": "e", "p2": "cen"},
        {"id": "l1", "type": "line", "p1": "cen", "p2": "s"},
    ]
    positions = {"cen": (0, 0), "s": (10, 0), "e": (0, 10)}
    edges, err = WireOrderer().order(entities, positions, {})
    assert err is None
    arc = [e for e in edges if e["kind"] == "arc"][0]
    (mx, my) = arc["points"][1]
    assert math.isclose(mx, 10 / math.sqrt(2), abs_tol=1e-6)
    assert math.isclose(my, 10 / math.sqrt(2), abs_tol=1e-6)


def test_open_loop_is_error():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [10, 0]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    edges, err = WireOrderer().order(entities, {"p0": (0, 0), "p1": (10, 0)}, {})
    assert err is not None and edges == []
