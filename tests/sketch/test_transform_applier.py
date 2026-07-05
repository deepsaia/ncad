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
