from ncad.sketch.wire_orderer import WireOrderer, _endpoints


def test_lone_ellipse_emits_ellipse_descriptor():
    entities = [{"id": "e", "type": "ellipse", "center": "c", "major_axis_end": "m",
                 "minor_radius": 2.0}]
    positions = {"c": (0.0, 0.0), "m": (5.0, 0.0)}
    edges, err = WireOrderer().order(entities, positions, {})
    assert err is None
    assert edges == [{"kind": "ellipse", "center": (0.0, 0.0),
                      "major_axis_end": (5.0, 0.0), "minor_radius": 2.0}]


def test_ellipse_with_connective_is_rejected():
    entities = [
        {"id": "e", "type": "ellipse", "center": "c", "major_axis_end": "m",
         "minor_radius": 2.0},
        {"id": "ln", "type": "line", "p1": "a", "p2": "b"},
    ]
    edges, err = WireOrderer().order(entities, {}, {})
    assert edges == [] and err is not None


def test_ellipse_arc_endpoints():
    arc = {"id": "e", "type": "ellipse_arc", "center": "c", "major_axis_end": "m",
           "minor_radius": 2.0, "start": "s", "end": "t"}
    assert _endpoints(arc) == ("s", "t")


def test_ellipse_arc_in_closed_loop_emits_descriptor():
    # An ellipse_arc from s->t, closed back by a line t->s.
    entities = [
        {"id": "ea", "type": "ellipse_arc", "center": "c", "major_axis_end": "m",
         "minor_radius": 2.0, "start": "s", "end": "t"},
        {"id": "ln", "type": "line", "p1": "t", "p2": "s"},
    ]
    positions = {"c": (0.0, 0.0), "m": (5.0, 0.0), "s": (5.0, 0.0), "t": (-5.0, 0.0)}
    edges, err = WireOrderer().order(entities, positions, {})
    assert err is None
    kinds = {e["kind"] for e in edges}
    assert kinds == {"ellipse_arc", "line"}
    ea = next(e for e in edges if e["kind"] == "ellipse_arc")
    assert ea["center"] == (0.0, 0.0) and ea["minor_radius"] == 2.0
    assert set(ea["points"]) == {(5.0, 0.0), (-5.0, 0.0)}
