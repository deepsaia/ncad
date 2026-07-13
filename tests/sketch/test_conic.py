from ncad.sketch.slvs_solver import _defining_points, _missing_reference
from ncad.sketch.wire_orderer import WireOrderer, _endpoints


def test_conic_defining_points():
    c = {"id": "k", "type": "conic", "start": "s", "apex": "a", "end": "t", "rho": 0.5}
    assert _defining_points(c) == ["s", "a", "t"]


def test_conic_endpoints_exclude_apex():
    c = {"id": "k", "type": "conic", "start": "s", "apex": "a", "end": "t", "rho": 0.5}
    assert _endpoints(c) == ("s", "t")


def test_conic_missing_apex_reported():
    entities = [
        {"id": "s", "type": "point", "at": [0, 0]},
        {"id": "t", "type": "point", "at": [10, 0]},
        {"id": "k", "type": "conic", "start": "s", "apex": "NOPE", "end": "t", "rho": 0.5},
    ]
    msg = _missing_reference(entities, [], {e["id"]: e for e in entities})
    assert msg is not None and "NOPE" in msg


def test_conic_descriptor_in_loop():
    # conic s->t plus a line t->s closing the loop.
    entities = [
        {"id": "k", "type": "conic", "start": "s", "apex": "a", "end": "t", "rho": 0.6},
        {"id": "ln", "type": "line", "p1": "t", "p2": "s"},
    ]
    positions = {"s": (0.0, 0.0), "a": (5.0, 5.0), "t": (10.0, 0.0)}
    edges, err = WireOrderer().order(entities, positions, {})
    assert err is None
    conic = next(e for e in edges if e["kind"] == "conic")
    assert conic["rho"] == 0.6
    assert conic["points"][1] == (5.0, 5.0)   # apex stays the middle control point
    assert {conic["points"][0], conic["points"][2]} == {(0.0, 0.0), (10.0, 0.0)}
