from ncad.sketch.entity_expander import EntityExpander


def test_arc_polar_lowers_to_arc_with_seeded_endpoints():
    entities = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "a", "type": "arc_polar", "center": "c", "radius": 10.0,
         "start_angle": 0.0, "sweep": 90.0},
    ]
    out = EntityExpander().expand(entities)
    by_id = {e["id"]: e for e in out}
    # The center point passes through unchanged.
    assert by_id["c"]["type"] == "point"
    # Two child points seeded on the circle at start_angle and start_angle+sweep.
    start = by_id["a/start"]
    end = by_id["a/end"]
    assert start["type"] == "point" and end["type"] == "point"
    assert start["at"][0] == 10.0 and abs(start["at"][1]) < 1e-9          # angle 0 deg
    assert abs(end["at"][0]) < 1e-9 and abs(end["at"][1] - 10.0) < 1e-9   # angle 90 deg
    # Derived endpoints are fixed, so an arc_polar is well-constrained by construction.
    assert start["fixed"] is True and end["fixed"] is True
    # An arc referencing the center + the two child points.
    arc = by_id["a"]
    assert arc["type"] == "arc"
    assert arc["center"] == "c" and arc["start"] == "a/start" and arc["end"] == "a/end"


def test_arc_polar_negative_sweep_seeds_clockwise_end():
    entities = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "a", "type": "arc_polar", "center": "c", "radius": 5.0,
         "start_angle": 90.0, "sweep": -90.0},
    ]
    by_id = {e["id"]: e for e in EntityExpander().expand(entities)}
    end = by_id["a/end"]
    # 90 - 90 = 0 deg -> (5, 0)
    assert abs(end["at"][0] - 5.0) < 1e-9 and abs(end["at"][1]) < 1e-9
