from ncad.sketch.slvs_solver import SlvsSolver


def test_spline_with_missing_point_reports_issue():
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [2.0, 2.0]},
        {"id": "bz", "type": "bezier", "points": ["p0", "p1", "ghost"]},
    ]
    result = SlvsSolver().solve(entities, [], "sk")
    assert result.status == "inconsistent"
    assert any("ghost" in i.message for i in result.issues)


def test_spline_with_present_points_solves():
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [2.0, 2.0]},
        {"id": "p2", "type": "point", "at": [4.0, 0.0]},
        {"id": "sp", "type": "interpolated", "points": ["p0", "p1", "p2"]},
    ]
    result = SlvsSolver().solve(entities, [], "sk")
    assert result.status != "inconsistent"
    assert "p1" in result.positions
