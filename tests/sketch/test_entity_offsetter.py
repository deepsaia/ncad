import pytest

from ncad.sketch.entity_offsetter import EntityOffsetter


def _line_setup():
    return {
        "p0": {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        "p1": {"id": "p1", "type": "point", "at": [10.0, 0.0]},
        "l": {"id": "l", "type": "line", "p1": "p0", "p2": "p1"},
    }


def test_line_offsets_along_left_normal():
    by_id = _line_setup()
    out = EntityOffsetter().offset(by_id["l"], by_id, 3.0, "o")
    line = [e for e in out if e["type"] == "line"][0]
    pts = {e["id"]: e["at"] for e in out if e["type"] == "point"}
    # left normal of +x direction is +y, so both endpoints move to y = 3
    assert round(pts[line["p1"]][1], 6) == 3.0
    assert round(pts[line["p2"]][1], 6) == 3.0
    assert all(e.get("fixed") for e in out)


def test_line_offset_negative_flips_side():
    by_id = _line_setup()
    out = EntityOffsetter().offset(by_id["l"], by_id, -4.0, "o")
    pts = [e for e in out if e["type"] == "point"]
    assert all(round(e["at"][1], 6) == -4.0 for e in pts)


def test_circle_offset_changes_radius():
    by_id = {
        "c": {"id": "c", "type": "point", "at": [0.0, 0.0]},
        "circ": {"id": "circ", "type": "circle", "center": "c", "radius": 10.0},
    }
    out = EntityOffsetter().offset(by_id["circ"], by_id, -3.0, "o")
    circ = [e for e in out if e["type"] == "circle"][0]
    assert circ["radius"] == 7.0
    assert circ.get("fixed")


def test_arc_offset_changes_radius_keeps_span():
    by_id = {
        "c": {"id": "c", "type": "point", "at": [0.0, 0.0]},
        "s": {"id": "s", "type": "point", "at": [5.0, 0.0]},
        "e": {"id": "e", "type": "point", "at": [0.0, 5.0]},
        "arc": {"id": "arc", "type": "arc", "center": "c", "start": "s", "end": "e"},
    }
    out = EntityOffsetter().offset(by_id["arc"], by_id, 2.0, "o")
    arc = [e for e in out if e["type"] == "arc"][0]
    assert arc["radius"] == 7.0  # 5 (seed radius) + 2


def test_zero_length_line_raises():
    by_id = {
        "p0": {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        "p1": {"id": "p1", "type": "point", "at": [0.0, 0.0]},
        "l": {"id": "l", "type": "line", "p1": "p0", "p2": "p1"},
    }
    with pytest.raises(ValueError):
        EntityOffsetter().offset(by_id["l"], by_id, 3.0, "o")
