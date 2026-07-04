from ncad.sketch.slvs_solver import SlvsSolver


def _square(with_second_distance=True):
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [30, 2]},
        {"id": "p2", "type": "point", "at": [31, 33]},
        {"id": "p3", "type": "point", "at": [1, 29]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
        {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
        {"id": "l2", "type": "line", "p1": "p2", "p2": "p3"},
        {"id": "l3", "type": "line", "p1": "p3", "p2": "p0"},
    ]
    constraints = [
        {"type": "horizontal", "of": "l0"},
        {"type": "vertical", "of": "l1"},
        {"type": "horizontal", "of": "l2"},
        {"type": "vertical", "of": "l3"},
        {"type": "distance", "points": ["p0", "p1"], "value": 40},
    ]
    if with_second_distance:
        constraints.append({"type": "distance", "points": ["p1", "p2"], "value": 40})
    return entities, constraints


def test_fully_constrained_square_solves():
    entities, constraints = _square()
    result = SlvsSolver().solve(entities, constraints, "sk")

    assert result.status in ("well_constrained", "under_constrained")
    (x0, y0), (x1, y1) = result.positions["p0"], result.positions["p1"]
    assert abs((x1 - x0) - 40) < 1e-6 and abs(y1 - y0) < 1e-6
    (x2, y2) = result.positions["p2"]
    assert abs(x2 - x1) < 1e-6 and abs(abs(y2 - y1) - 40) < 1e-6


def test_under_constrained_reports_warning_and_positions():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [5, 0]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    constraints = [{"type": "distance", "points": ["p0", "p1"], "value": 40}]
    result = SlvsSolver().solve(entities, constraints, "sk")

    assert result.status == "under_constrained" and result.dof > 0
    assert result.positions and "p0" in result.positions
    assert any(i.level == "warning" for i in result.issues)


def test_inconsistent_reports_error():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [5, 0]},
        {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    constraints = [
        {"type": "distance", "points": ["p0", "p1"], "value": 10},
        {"type": "distance", "points": ["p0", "p1"], "value": 20},
    ]
    result = SlvsSolver().solve(entities, constraints, "sk")

    assert result.status == "inconsistent"
    assert any(i.level == "error" and i.node_id == "sk" for i in result.issues)


def test_unknown_entity_reference_is_error():
    entities = [{"id": "p0", "type": "point", "at": [0, 0]}]
    constraints = [{"type": "distance", "points": ["p0", "ghost"], "value": 10}]
    result = SlvsSolver().solve(entities, constraints, "sk")

    assert result.status == "inconsistent"
    assert any(i.node_id == "sk" for i in result.issues)
