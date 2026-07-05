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


def _right_angle_corner():
    # two lines meeting at the origin corner `c`: one along +x, one along +y
    return [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "ex", "type": "point", "at": [10.0, 0.0]},
        {"id": "ey", "type": "point", "at": [0.0, 10.0]},
        {"id": "lx", "type": "line", "p1": "c", "p2": "ex"},
        {"id": "ly", "type": "line", "p1": "c", "p2": "ey"},
    ]


def test_fillet_inserts_tangent_arc():
    out = TopologyApplier().apply(_right_angle_corner(), [
        {"op": "fillet", "at": "c", "radius": 3.0}])
    arc = [e for e in out if e["type"] == "arc" and e["id"] == "c/fillet/arc"][0]
    center = [e for e in out if e["id"] == "c/fillet/c"][0]
    # a 90-degree corner at origin with r=3 puts the arc center at (3,3)
    assert (round(center["at"][0], 6), round(center["at"][1], 6)) == (3.0, 3.0)
    # tangent points are (3,0) and (0,3)
    ta = [e for e in out if e["id"] == "c/fillet/a"][0]
    tb = [e for e in out if e["id"] == "c/fillet/b"][0]
    tangents = {(round(ta["at"][0], 6), round(ta["at"][1], 6)),
                (round(tb["at"][0], 6), round(tb["at"][1], 6))}
    assert tangents == {(3.0, 0.0), (0.0, 3.0)}
    lx = [e for e in out if e["id"] == "lx"][0]
    assert "c" not in {lx["p1"], lx["p2"]}
    assert arc.get("fixed")


def test_chamfer_inserts_line():
    out = TopologyApplier().apply(_right_angle_corner(), [
        {"op": "chamfer", "at": "c", "setback": 4.0}])
    seg = [e for e in out if e["type"] == "line" and e["id"] == "c/chamfer/line"][0]
    a = [e for e in out if e["id"] == "c/chamfer/a"][0]
    b = [e for e in out if e["id"] == "c/chamfer/b"][0]
    pts = {(round(a["at"][0], 6), round(a["at"][1], 6)),
           (round(b["at"][0], 6), round(b["at"][1], 6))}
    assert pts == {(4.0, 0.0), (0.0, 4.0)}
    assert {seg["p1"], seg["p2"]} == {"c/chamfer/a", "c/chamfer/b"}


def test_fillet_non_positive_radius_raises():
    with pytest.raises(TopologyError):
        TopologyApplier().apply(_right_angle_corner(), [
            {"op": "fillet", "at": "c", "radius": 0.0}])


def test_corner_not_shared_by_two_raises():
    ents = _right_angle_corner()
    ents.append({"id": "ez", "type": "point", "at": [-10.0, 0.0]})
    ents.append({"id": "lz", "type": "line", "p1": "c", "p2": "ez"})
    with pytest.raises(TopologyError):
        TopologyApplier().apply(ents, [{"op": "fillet", "at": "c", "radius": 3.0}])


def test_fillet_non_line_corner_raises():
    ents = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "cc", "type": "point", "at": [0.0, 5.0]},
        {"id": "ex", "type": "point", "at": [10.0, 0.0]},
        {"id": "ee", "type": "point", "at": [5.0, 0.0]},
        {"id": "lx", "type": "line", "p1": "c", "p2": "ex"},
        {"id": "arc0", "type": "arc", "center": "cc", "start": "c", "end": "ee"},
    ]
    with pytest.raises(TopologyError):
        TopologyApplier().apply(ents, [{"op": "fillet", "at": "c", "radius": 2.0}])


def _open_line():
    return [
        {"id": "a", "type": "point", "at": [0.0, 0.0]},
        {"id": "b", "type": "point", "at": [10.0, 0.0]},
        {"id": "seg", "type": "line", "p1": "a", "p2": "b"},
    ]


def test_split_line_into_two_at_interior_point():
    out = TopologyApplier().apply(_open_line(), [
        {"id": "s", "op": "split", "of": "seg", "at": [4.0, 0.0]}])
    cut = [e for e in out if e["id"] == "s/x"][0]
    assert (round(cut["at"][0], 6), round(cut["at"][1], 6)) == (4.0, 0.0)
    halves = [e for e in out if e["type"] == "line" and e["id"] in ("s/0", "s/1")]
    assert len(halves) == 2
    endpoints = {p for h in halves for p in (h["p1"], h["p2"])}
    assert "s/x" in endpoints and "a" in endpoints and "b" in endpoints
    assert not [e for e in out if e["id"] == "seg"]


def test_split_point_projected_onto_line():
    out = TopologyApplier().apply(_open_line(), [
        {"id": "s", "op": "split", "of": "seg", "at": [4.0, 9.0]}])
    cut = [e for e in out if e["id"] == "s/x"][0]
    assert (round(cut["at"][0], 6), round(cut["at"][1], 6)) == (4.0, 0.0)


def test_split_point_off_segment_raises():
    with pytest.raises(TopologyError):
        TopologyApplier().apply(_open_line(), [
            {"id": "s", "op": "split", "of": "seg", "at": [20.0, 0.0]}])


def test_split_arc_into_two_arcs():
    import math
    ents = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "s", "type": "point", "at": [5.0, 0.0]},
        {"id": "e", "type": "point", "at": [0.0, 5.0]},
        {"id": "arc", "type": "arc", "center": "c", "start": "s", "end": "e"},
    ]
    out = TopologyApplier().apply(ents, [
        {"id": "sp", "op": "split", "of": "arc", "at": [3.5355, 3.5355]}])
    arcs = [e for e in out if e["type"] == "arc" and e["id"] in ("sp/0", "sp/1")]
    assert len(arcs) == 2
    assert all(a["center"] == "c" for a in arcs)
    cut = [e for e in out if e["id"] == "sp/x"][0]
    assert round(math.hypot(cut["at"][0], cut["at"][1]), 3) == 5.0


def _square_loop():
    return [
        {"id": "bl", "type": "point", "at": [0.0, 0.0]},
        {"id": "br", "type": "point", "at": [20.0, 0.0]},
        {"id": "tr", "type": "point", "at": [20.0, 20.0]},
        {"id": "tl", "type": "point", "at": [0.0, 20.0]},
        {"id": "bottom", "type": "line", "p1": "bl", "p2": "br"},
        {"id": "right", "type": "line", "p1": "br", "p2": "tr"},
        {"id": "top", "type": "line", "p1": "tr", "p2": "tl"},
        {"id": "left", "type": "line", "p1": "tl", "p2": "bl"},
    ]


def test_loop_offset_inward_mitre_makes_smaller_square():
    out = TopologyApplier().apply(_square_loop(), [
        {"id": "in", "op": "loop_offset",
         "entities": ["bottom", "right", "top", "left"], "distance": -4.0}])
    assert not [e for e in out if e["id"] in ("bottom", "right", "top", "left")]
    edges = [e for e in out if e["type"] == "line" and e["id"].startswith("in/e")]
    corners = [e for e in out if e["type"] == "point" and e["id"].startswith("in/c")]
    assert len(edges) == 4 and len(corners) == 4
    xy = {(round(c["at"][0], 6), round(c["at"][1], 6)) for c in corners}
    assert xy == {(4.0, 4.0), (16.0, 4.0), (16.0, 16.0), (4.0, 16.0)}
    assert all(e.get("fixed") for e in edges)


def test_loop_offset_open_loop_raises():
    ents = [e for e in _square_loop() if e["id"] != "left"]
    with pytest.raises(TopologyError):
        TopologyApplier().apply(ents, [
            {"id": "in", "op": "loop_offset",
             "entities": ["bottom", "right", "top"], "distance": -4.0}])


def test_loop_offset_collapsing_distance_raises():
    with pytest.raises(TopologyError):
        TopologyApplier().apply(_square_loop(), [
            {"id": "in", "op": "loop_offset",
             "entities": ["bottom", "right", "top", "left"], "distance": -20.0}])


def test_loop_offset_round_makes_rounded_corners():
    out = TopologyApplier().apply(_square_loop(), [
        {"id": "in", "op": "loop_offset",
         "entities": ["bottom", "right", "top", "left"],
         "distance": -4.0, "corner": "round"}])
    arcs = [e for e in out if e["type"] == "arc" and e["id"].startswith("in/arc")]
    edges = [e for e in out if e["type"] == "line" and e["id"].startswith("in/e")]
    assert len(arcs) == 4 and len(edges) == 4
    assert all(round(a["radius"], 6) == 4.0 for a in arcs)
    assert all(e.get("fixed") for e in arcs)
