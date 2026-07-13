from ncad.sketch.slvs_solver import SlvsSolver


def _arc_line():
    return (
        [
            {"id": "c", "type": "point", "at": [0.0, 0.0]},
            {"id": "s", "type": "point", "at": [5.0, 0.0]},
            {"id": "e", "type": "point", "at": [0.0, 5.0]},
            {"id": "arc", "type": "arc", "center": "c", "start": "s", "end": "e"},
            {"id": "p2", "type": "point", "at": [0.0, 10.0]},
            {"id": "ln", "type": "line", "p1": "e", "p2": "p2"},
        ],
        [{"type": "smooth", "of": ["arc", "ln"]}],
    )


def test_smooth_g1_arc_line_solves():
    entities, constraints = _arc_line()
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status in ("well_constrained", "under_constrained")


def test_smooth_g2_refuses_clearly():
    entities, constraints = _arc_line()
    constraints[0]["continuity"] = "g2"
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status == "inconsistent"
    assert any("g2" in i.message.lower() or "curvature" in i.message.lower()
               for i in result.issues)


def test_smooth_on_point_defined_curve_refuses():
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [5.0, 5.0]},
        {"id": "p2", "type": "point", "at": [10.0, 0.0]},
        {"id": "sp", "type": "interpolated", "points": ["p0", "p1", "p2"]},
        {"id": "p3", "type": "point", "at": [15.0, 0.0]},
        {"id": "ln", "type": "line", "p1": "p2", "p2": "p3"},
    ]
    result = SlvsSolver().solve(entities, [{"type": "smooth", "of": ["sp", "ln"]}], "sk")
    assert result.status == "inconsistent"
    assert any("point-defined" in i.message.lower() or "spline" in i.message.lower()
               for i in result.issues)
