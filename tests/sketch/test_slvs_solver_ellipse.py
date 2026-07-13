from ncad.sketch.slvs_solver import SlvsSolver, _defining_points, _missing_reference


def test_ellipse_defining_points():
    ell = {"id": "e", "type": "ellipse", "center": "c", "major_axis_end": "m",
           "minor_radius": 2.0}
    assert _defining_points(ell) == ["c", "m"]


def test_ellipse_arc_defining_points():
    arc = {"id": "e", "type": "ellipse_arc", "center": "c", "major_axis_end": "m",
           "minor_radius": 2.0, "start": "s", "end": "t"}
    assert _defining_points(arc) == ["c", "m", "s", "t"]


def test_ellipse_missing_point_reported():
    entities = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "e", "type": "ellipse", "center": "c", "major_axis_end": "NOPE",
         "minor_radius": 2.0},
    ]
    msg = _missing_reference(entities, [], {e["id"]: e for e in entities})
    assert msg is not None and "NOPE" in msg


def test_ellipse_solves_points_into_positions():
    entities = [
        {"id": "c", "type": "point", "at": [0.0, 0.0]},
        {"id": "m", "type": "point", "at": [5.0, 0.0]},
        {"id": "e", "type": "ellipse", "center": "c", "major_axis_end": "m",
         "minor_radius": 2.0},
    ]
    constraints = [{"type": "fix", "of": "c"}, {"type": "fix", "of": "m"}]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status in ("well_constrained", "under_constrained")
    assert result.positions["c"] == (0.0, 0.0)
    assert abs(result.positions["m"][0] - 5.0) < 1e-9
