from ncad.sketch.entity_expander import EntityExpander


def test_primitives_pass_through_unchanged():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p0"},
        {"id": "c0", "type": "circle", "center": "p0", "radius": 5},
        {"id": "a0", "type": "arc", "center": "p0", "start": "p0", "end": "p0"},
    ]
    assert EntityExpander().expand(entities) == entities


def test_polyline_expands_to_lines():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [10, 0]},
        {"id": "p2", "type": "point", "at": [10, 10]},
        {"id": "pl", "type": "polyline", "points": ["p0", "p1", "p2"]},
    ]
    out = EntityExpander().expand(entities)
    lines = [e for e in out if e.get("type") == "line"]
    assert [(e["p1"], e["p2"]) for e in lines] == [("p0", "p1"), ("p1", "p2")]
    assert all(e["id"].startswith("pl/") for e in lines)


def test_regular_polygon_expands_to_points_and_lines():
    entities = [
        {"id": "hc", "type": "point", "at": [0, 0]},
        {"id": "hex", "type": "polygon", "center": "hc", "sides": 6, "r": 20},
    ]
    out = EntityExpander().expand(entities)
    pts = [e for e in out if e.get("type") == "point" and e["id"].startswith("hex/")]
    lines = [e for e in out if e.get("type") == "line" and e["id"].startswith("hex/")]
    assert len(pts) == 6 and len(lines) == 6
    assert lines[-1]["p2"] == lines[0]["p1"]


def test_slot_expands_to_two_lines_and_two_arcs():
    entities = [
        {"id": "a", "type": "point", "at": [0, 0]},
        {"id": "b", "type": "point", "at": [30, 0]},
        {"id": "sl", "type": "slot", "p1": "a", "p2": "b", "width": 10},
    ]
    out = EntityExpander().expand(entities)
    lines = [e for e in out if e.get("type") == "line" and e["id"].startswith("sl/")]
    arcs = [e for e in out if e.get("type") == "arc" and e["id"].startswith("sl/")]
    assert len(lines) == 2 and len(arcs) == 2
