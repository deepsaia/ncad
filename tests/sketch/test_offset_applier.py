import pytest

from ncad.sketch.offset_applier import OffsetApplier, OffsetError


def _line(distance):
    return [
        {"id": "pa", "type": "point", "at": [0, 0]},
        {"id": "pb", "type": "point", "at": [10, 0]},
        {"id": "l0", "type": "line", "p1": "pa", "p2": "pb", "construction": True},
        {"id": "o0", "type": "offset", "from": "l0", "distance": distance},
    ]


def test_offset_line_is_parallel_and_real():
    out = OffsetApplier().apply(_line(3))
    line = [e for e in out if e["type"] == "line" and e["id"] == "o0"][0]
    assert not line.get("construction")
    pts = [e for e in out if e["type"] == "point" and e["id"].startswith("o0/")]
    ys = sorted(round(e["at"][1], 3) for e in pts)
    assert ys == [3.0, 3.0]


def test_negative_offset_flips_side():
    out = OffsetApplier().apply(_line(-4))
    pts = [e for e in out if e["type"] == "point" and e["id"].startswith("o0/")]
    assert all(round(e["at"][1], 3) == -4.0 for e in pts)


def test_offset_circle_changes_radius():
    entities = [
        {"id": "cp", "type": "point", "at": [0, 0]},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 10, "construction": True},
        {"id": "o0", "type": "offset", "from": "c0", "distance": -3},
    ]
    out = OffsetApplier().apply(entities)
    circle = [e for e in out if e["type"] == "circle" and e["id"] == "o0"][0]
    assert circle["radius"] == 7 and not circle.get("construction")


def test_unknown_source_raises():
    entities = [{"id": "o0", "type": "offset", "from": "ghost", "distance": 1}]
    with pytest.raises(OffsetError):
        OffsetApplier().apply(entities)


def test_non_offset_entities_pass_through():
    entities = [{"id": "p0", "type": "point", "at": [1, 2]}]
    assert OffsetApplier().apply(entities) == entities


def test_offset_circle_gets_fresh_center_and_fixed_flag():
    entities = [
        {"id": "cp", "type": "point", "at": [1, 2]},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 10, "construction": True},
        {"id": "o0", "type": "offset", "from": "c0", "distance": -3},
    ]
    out = OffsetApplier().apply(entities)
    circle = [e for e in out if e["type"] == "circle" and e["id"] == "o0"][0]
    # a fresh, real (non-construction) center at the source location; fixed size
    assert circle["center"] == "o0/c" and circle.get("fixed") is True
    center = [e for e in out if e["id"] == "o0/c"][0]
    assert center["at"] == [1, 2] and not center.get("construction")
