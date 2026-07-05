import pytest

from ncad.sketch.transform_applier import TransformApplier, TransformError


def _triangle():
    # three points + three lines forming a closed loop
    return [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [10.0, 0.0]},
        {"id": "p2", "type": "point", "at": [0.0, 10.0]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
        {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
        {"id": "l2", "type": "line", "p1": "p2", "p2": "p0"},
    ]


def test_absent_transforms_is_noop():
    ents = _triangle()
    out = TransformApplier().apply(ents, [])
    assert out == ents


def test_move_replaces_points_in_place():
    out = TransformApplier().apply(_triangle(), [
        {"op": "move", "sources": ["p0", "p1", "p2", "l0", "l1", "l2"],
         "dx": 5.0, "dy": -2.0}])
    p0 = [e for e in out if e["id"] == "p0"][0]
    assert p0["at"] == [5.0, -2.0]
    # ids are reused (in-place), so still exactly 6 entities
    assert len(out) == 6
    assert all(e.get("fixed") for e in out if e["type"] == "point")


def test_rotate_about_origin():
    out = TransformApplier().apply(_triangle(), [
        {"op": "rotate", "sources": ["p0", "p1", "p2"], "center": [0.0, 0.0],
         "angle": 90.0}])
    p1 = [e for e in out if e["id"] == "p1"][0]
    assert round(p1["at"][0], 6) == 0.0 and round(p1["at"][1], 6) == 10.0


def test_scale_scales_circle_radius():
    ents = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "circ", "type": "circle", "center": "c", "radius": 4.0},
    ]
    out = TransformApplier().apply(ents, [
        {"op": "scale", "sources": ["c", "circ"], "center": [0.0, 0.0], "factor": 2.0}])
    circ = [e for e in out if e["id"] == "circ"][0]
    assert circ["radius"] == 8.0


def test_sugar_id_resolves_children():
    ents = [
        {"id": "poly/p/0", "type": "point", "at": [0.0, 0.0]},
        {"id": "poly/p/1", "type": "point", "at": [2.0, 0.0]},
        {"id": "poly/l/0", "type": "line", "p1": "poly/p/0", "p2": "poly/p/1"},
    ]
    out = TransformApplier().apply(ents, [
        {"op": "move", "sources": ["poly"], "dx": 1.0, "dy": 0.0}])
    p0 = [e for e in out if e["id"] == "poly/p/0"][0]
    assert p0["at"] == [1.0, 0.0]


def test_unknown_op_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_triangle(), [{"op": "warp", "sources": ["p0"]}])


def test_empty_sources_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_triangle(), [
            {"op": "move", "sources": ["nope"], "dx": 1.0, "dy": 0.0}])


def test_zero_scale_factor_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_triangle(), [
            {"op": "scale", "sources": ["p0"], "center": [0.0, 0.0], "factor": 0.0}])


def _half_vee():
    # an open two-segment chain to be mirrored across the Y axis into a closed vee
    return [
        {"id": "apex", "type": "point", "at": [0.0, 0.0]},
        {"id": "top", "type": "point", "at": [0.0, 10.0]},
        {"id": "right", "type": "point", "at": [5.0, 5.0]},
        {"id": "s0", "type": "line", "p1": "top", "p2": "right"},
        {"id": "s1", "type": "line", "p1": "right", "p2": "apex"},
    ]


def test_mirror_reflects_and_appends_copies():
    out = TransformApplier().apply(_half_vee(), [
        {"id": "m", "op": "mirror", "sources": ["s0", "s1"],
         "axis": {"p1": "apex", "p2": "top"}}])
    ids = {e["id"] for e in out}
    assert {"s0", "s1"}.issubset(ids)
    mirror_lines = [e for e in out if e["type"] == "line" and e["id"].startswith("m/")]
    assert len(mirror_lines) == 2
    mirrored_pts = [e for e in out if e["type"] == "point" and e["id"].startswith("m/")]
    xs = sorted(round(e["at"][0], 6) for e in mirrored_pts)
    assert -5.0 in xs


def test_mirror_shares_points_on_axis():
    out = TransformApplier().apply(_half_vee(), [
        {"id": "m", "op": "mirror", "sources": ["s0", "s1"],
         "axis": {"p1": "apex", "p2": "top"}}])
    mirrored_pts = [e for e in out if e["type"] == "point" and e["id"].startswith("m/")]
    # apex(0,0) and top(0,10) are on the axis, right(5,5) reflects: 3 distinct points
    assert len(mirrored_pts) == 3


def test_linear_pattern_replicates_count_copies():
    ents = [
        {"id": "a", "type": "point", "at": [0.0, 0.0]},
        {"id": "b", "type": "point", "at": [1.0, 0.0]},
        {"id": "seg", "type": "line", "p1": "a", "p2": "b"},
    ]
    out = TransformApplier().apply(ents, [
        {"id": "row", "op": "pattern", "sources": ["a", "b", "seg"],
         "kind": "linear", "count": 4, "dx": 10.0, "dy": 0.0}])
    copy_lines = [e for e in out if e["type"] == "line" and e["id"].startswith("row/")]
    assert len(copy_lines) == 3
    xs = sorted(round(e["at"][0], 6) for e in out
                if e["type"] == "point" and e["id"].startswith("row/"))
    assert 30.0 in xs


def test_circular_pattern_spaces_by_angle():
    ents = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "tooth", "type": "circle", "center": "c", "radius": 1.0},
    ]
    out = TransformApplier().apply(ents, [
        {"id": "ring", "op": "pattern", "sources": ["c", "tooth"],
         "kind": "circular", "count": 4, "center": [10.0, 0.0]}])
    copy_centers = [e for e in out if e["type"] == "point" and e["id"].startswith("ring/")]
    assert len(copy_centers) == 3


def test_mirror_missing_axis_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_half_vee(), [
            {"id": "m", "op": "mirror", "sources": ["s0"]}])


def test_pattern_missing_id_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_half_vee(), [
            {"op": "pattern", "sources": ["s0"], "kind": "linear", "count": 2,
             "dx": 1.0, "dy": 0.0}])


def test_pattern_count_below_one_raises():
    with pytest.raises(TransformError):
        TransformApplier().apply(_half_vee(), [
            {"id": "p", "op": "pattern", "sources": ["s0"], "kind": "linear",
             "count": 0, "dx": 1.0, "dy": 0.0}])


def test_pattern_copy_ids_padded_past_ten():
    ents = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "t", "type": "circle", "center": "c", "radius": 1.0},
    ]
    out = TransformApplier().apply(ents, [
        {"id": "ring", "op": "pattern", "sources": ["c", "t"], "kind": "linear",
         "count": 12, "dx": 5.0, "dy": 0.0}])
    circ_ids = sorted(e["id"] for e in out
                      if e["type"] == "circle" and e["id"].startswith("ring/"))
    assert circ_ids == sorted(circ_ids)
    assert any("/00/" in i for i in circ_ids)
