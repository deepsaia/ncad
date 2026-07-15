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


def test_circle_with_radius_constraint_solves():
    entities = [
        {"id": "cp", "type": "point", "at": [0, 0]},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 5},
    ]
    constraints = [{"type": "radius", "of": "c0", "value": 10}]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status in ("well_constrained", "under_constrained")
    assert abs(result.radii["c0"] - 10.0) < 1e-6


def test_arc_endpoints_are_equidistant_from_center():
    import math
    entities = [
        {"id": "cen", "type": "point", "at": [0, 0]},
        {"id": "s", "type": "point", "at": [10, 0]},
        {"id": "e", "type": "point", "at": [0, 9]},
        {"id": "arc", "type": "arc", "center": "cen", "start": "s", "end": "e"},
    ]
    constraints = [{"type": "distance", "points": ["cen", "s"], "value": 10}]
    result = SlvsSolver().solve(entities, constraints, "sk")
    (cx, cy) = result.positions["cen"]
    (ex, ey) = result.positions["e"]
    assert math.isclose(math.hypot(ex - cx, ey - cy), 10.0, abs_tol=1e-6)


def test_conflicting_radius_is_inconsistent():
    entities = [
        {"id": "cp", "type": "point", "at": [0, 0]},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 5},
    ]
    constraints = [
        {"type": "radius", "of": "c0", "value": 10},
        {"type": "radius", "of": "c0", "value": 20},
    ]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status == "inconsistent"


def test_unknown_circle_center_is_error():
    entities = [{"id": "c0", "type": "circle", "center": "ghost", "radius": 5}]
    result = SlvsSolver().solve(entities, [], "sk")
    assert result.status == "inconsistent"
    assert any(i.node_id == "sk" for i in result.issues)


def test_constraint_error_surfaces_as_inconsistent():
    entities = [
        {"id": "p0", "type": "point", "at": [0, 0]},
        {"id": "p1", "type": "point", "at": [10, 0]},
    ]
    constraints = [{"type": "distance", "points": ["p0", "p1"], "driven": True}]  # no id
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status == "inconsistent"
    assert any(i.node_id == "sk" for i in result.issues)


def _two_lines():
    return [
        {"id": "a", "type": "point", "at": [0, 0]},
        {"id": "b", "type": "point", "at": [10, 1]},
        {"id": "c", "type": "point", "at": [0, 5]},
        {"id": "d", "type": "point", "at": [10, 7]},
        {"id": "l0", "type": "line", "p1": "a", "p2": "b"},
        {"id": "l1", "type": "line", "p1": "c", "p2": "d"},
    ]


def test_parallel_makes_line_directions_equal():
    ents = _two_lines()
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "fix", "of": "c"}, {"type": "parallel", "lines": ["l0", "l1"]},
            {"type": "distance", "points": ["c", "d"], "value": 10.05}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert r.status in ("well_constrained", "under_constrained")
    (cx, cy), (dx, dy) = r.positions["c"], r.positions["d"]
    (ax, ay), (bx, by) = r.positions["a"], r.positions["b"]
    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
    assert abs(cross) < 1e-3


def test_perpendicular():
    ents = _two_lines()
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "fix", "of": "c"}, {"type": "perpendicular", "lines": ["l0", "l1"]},
            {"type": "distance", "points": ["c", "d"], "value": 10}]
    r = SlvsSolver().solve(ents, cons, "sk")
    (cx, cy), (dx, dy) = r.positions["c"], r.positions["d"]
    (ax, ay), (bx, by) = r.positions["a"], r.positions["b"]
    dot = (bx - ax) * (dx - cx) + (by - ay) * (dy - cy)
    assert abs(dot) < 1e-3


def test_equal_length_lines():
    import math
    ents = _two_lines()
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "fix", "of": "c"}, {"type": "equal", "of": ["l0", "l1"]},
            {"type": "horizontal", "of": "l1"}]
    r = SlvsSolver().solve(ents, cons, "sk")
    (ax, ay), (bx, by) = r.positions["a"], r.positions["b"]
    (cx, cy), (dx, dy) = r.positions["c"], r.positions["d"]
    assert math.isclose(math.hypot(bx - ax, by - ay), math.hypot(dx - cx, dy - cy),
                        abs_tol=1e-3)


def test_equal_line_and_circle_is_error():
    ents = [
        {"id": "a", "type": "point", "at": [0, 0]}, {"id": "b", "type": "point", "at": [10, 0]},
        {"id": "cp", "type": "point", "at": [0, 20]},
        {"id": "l0", "type": "line", "p1": "a", "p2": "b"},
        {"id": "c0", "type": "circle", "center": "cp", "radius": 5},
    ]
    r = SlvsSolver().solve(ents, [{"type": "equal", "of": ["l0", "c0"]}], "sk")
    assert r.status == "inconsistent"


def test_concentric_circles_share_center():
    ents = [
        {"id": "p0", "type": "point", "at": [0, 0]}, {"id": "p1", "type": "point", "at": [3, 1]},
        {"id": "c0", "type": "circle", "center": "p0", "radius": 5},
        {"id": "c1", "type": "circle", "center": "p1", "radius": 8},
    ]
    cons = [{"type": "fix", "of": "p0"}, {"type": "concentric", "of": ["c0", "c1"]}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert abs(r.positions["p1"][0]) < 1e-6 and abs(r.positions["p1"][1]) < 1e-6


def test_fix_anchors_a_line():
    ents = [
        {"id": "a", "type": "point", "at": [2, 3]}, {"id": "b", "type": "point", "at": [12, 3]},
        {"id": "l0", "type": "line", "p1": "a", "p2": "b"},
    ]
    r = SlvsSolver().solve(ents, [{"type": "fix", "of": "l0"}], "sk")
    assert r.dof == 0 and r.status == "well_constrained"
    assert r.positions["a"] == (2.0, 3.0) and r.positions["b"] == (12.0, 3.0)


def test_tangent_arc_line_solves():
    ents = [
        {"id": "cen", "type": "point", "at": [0, 0]},
        {"id": "s", "type": "point", "at": [10, 0]},
        {"id": "e", "type": "point", "at": [0, 10]},
        {"id": "lp", "type": "point", "at": [10, -8]},
        {"id": "arc", "type": "arc", "center": "cen", "start": "s", "end": "e"},
        {"id": "ln", "type": "line", "p1": "s", "p2": "lp"},
    ]
    cons = [{"type": "fix", "of": "cen"}, {"type": "fix", "of": "lp"},
            {"type": "distance", "points": ["cen", "s"], "value": 10},
            {"type": "tangent", "of": ["arc", "ln"]}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert r.status in ("well_constrained", "under_constrained")
    assert not any(i.level == "error" for i in r.issues)


def test_angle_drives_two_lines():
    import math
    ents = [
        {"id": "a", "type": "point", "at": [0, 0]}, {"id": "b", "type": "point", "at": [10, 0]},
        {"id": "c", "type": "point", "at": [7, 7]},
        {"id": "l0", "type": "line", "p1": "a", "p2": "b"},
        {"id": "l1", "type": "line", "p1": "a", "p2": "c"},
    ]
    cons = [{"type": "fix", "of": "a"}, {"type": "horizontal", "of": "l0"},
            {"type": "distance", "points": ["a", "b"], "value": 10},
            {"type": "distance", "points": ["a", "c"], "value": 10},
            {"type": "angle", "lines": ["l0", "l1"], "value": 60}]
    r = SlvsSolver().solve(ents, cons, "sk")
    (cx, cy) = r.positions["c"]
    assert math.isclose(math.degrees(math.atan2(cy, cx)), 60.0, abs_tol=0.5)


def test_diameter_sizes_a_circle():
    ents = [{"id": "cp", "type": "point", "at": [0, 0]},
            {"id": "c0", "type": "circle", "center": "cp", "radius": 3}]
    r = SlvsSolver().solve(ents, [{"type": "diameter", "of": "c0", "value": 20}], "sk")
    assert abs(r.radii["c0"] - 10.0) < 1e-6


def test_driven_distance_is_measured_not_enforced():
    ents = [
        {"id": "a", "type": "point", "at": [0, 0]}, {"id": "b", "type": "point", "at": [10, 0]},
    ]
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "distance", "points": ["a", "b"], "driven": True, "id": "len"}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert abs(r.measurements["len"] - 10.0) < 1e-6


def test_driven_dim_does_not_change_dof():
    ents = [{"id": "a", "type": "point", "at": [0, 0]}, {"id": "b", "type": "point", "at": [10, 0]}]
    with_driven = SlvsSolver().solve(ents, [
        {"type": "distance", "points": ["a", "b"], "driven": True, "id": "d"}], "sk")
    without = SlvsSolver().solve(ents, [], "sk")
    assert with_driven.dof == without.dof


def test_construction_entity_is_pinned():
    ents = [
        {"id": "a", "type": "point", "at": [3, 4], "construction": True},
        {"id": "b", "type": "point", "at": [9, 4], "construction": True},
        {"id": "l0", "type": "line", "p1": "a", "p2": "b", "construction": True},
    ]
    r = SlvsSolver().solve(ents, [], "sk")
    assert r.positions["a"] == (3.0, 4.0) and r.positions["b"] == (9.0, 4.0)
    assert r.dof == 0


def test_fixed_arc_redundant_pin_is_accepted():
    # A closed loop with a fixed fillet arc: two fixed lines meet a fixed tangent arc.
    # The arc's equal-radius coupling makes its point pins redundant (solver code 5, 0
    # failing constraints). SolveSpace still finds the correct positions, so we must
    # accept it as solved, not report it inconsistent. This mirrors what fillet emits.
    entities = [
        {"id": "bl", "type": "point", "at": [0.0, 0.0], "fixed": True},
        {"id": "ta", "type": "point", "at": [10.0, 0.0], "fixed": True},
        {"id": "tb", "type": "point", "at": [0.0, 10.0], "fixed": True},
        {"id": "cc", "type": "point", "at": [10.0, 10.0], "fixed": True},
        {"id": "bottom", "type": "line", "p1": "bl", "p2": "ta", "fixed": True},
        {"id": "left", "type": "line", "p1": "tb", "p2": "bl", "fixed": True},
        {"id": "arc", "type": "arc", "center": "cc", "start": "ta", "end": "tb",
         "fixed": True},
    ]
    result = SlvsSolver().solve(entities, [], "sk")
    assert result.status != "inconsistent"
    assert result.positions["ta"] == (10.0, 0.0)
    assert result.positions["tb"] == (0.0, 10.0)


def test_genuine_conflict_still_inconsistent():
    # Two conflicting distance constraints on the same segment must still report failure
    # (Failed is non-empty), so the redundant-but-consistent relaxation is not too broad.
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [10.0, 0.0]},
        {"id": "l", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    constraints = [
        {"type": "fix", "of": "p0"},
        {"type": "distance", "points": ["p0", "p1"], "value": 10},
        {"type": "distance", "points": ["p0", "p1"], "value": 20},
    ]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status == "inconsistent"


def test_fixed_point_drift_is_rejected():
    # A reported solve that leaves a fixed point far from its seed must be downgraded to
    # inconsistent by the safety net (masked over-pinning guard).
    from ncad.sketch import slvs_solver as m

    result = m._result_from(5, 0, [], {"p": (99.0, 99.0)}, "sk", {}, {}, drifted="p")
    assert result.status == "inconsistent"


def test_no_drift_solve_is_accepted():
    from ncad.sketch import slvs_solver as m

    result = m._result_from(5, 0, [], {"p": (0.0, 0.0)}, "sk", {}, {}, drifted=None)
    assert result.status != "inconsistent"


def test_overconstrained_reports_failing_constraint_ids():
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [10.0, 0.0]},
        {"id": "l", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    constraints = [
        {"id": "fix0", "type": "fix", "of": "p0"},
        {"id": "d_ten", "type": "distance", "points": ["p0", "p1"], "value": 10},
        {"id": "d_twenty", "type": "distance", "points": ["p0", "p1"], "value": 20},
    ]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.status == "inconsistent"
    assert any(fid in ("d_ten", "d_twenty") for fid in result.failing_ids)


def test_length_ratio_scales_one_line_to_another():
    import math
    ents = _two_lines()
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "fix", "of": "c"}, {"type": "horizontal", "of": "l1"},
            {"type": "length_ratio", "lines": ["l1", "l0"], "value": 2.0}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert r.status in ("well_constrained", "under_constrained")
    (ax, ay), (bx, by) = r.positions["a"], r.positions["b"]
    (cx, cy), (dx, dy) = r.positions["c"], r.positions["d"]
    len_l0 = math.hypot(bx - ax, by - ay)
    len_l1 = math.hypot(dx - cx, dy - cy)
    assert math.isclose(len_l1, 2.0 * len_l0, rel_tol=1e-3)


def test_length_difference_sets_the_gap():
    import math
    ents = _two_lines()
    cons = [{"type": "fix", "of": "a"}, {"type": "fix", "of": "b"},
            {"type": "fix", "of": "c"}, {"type": "horizontal", "of": "l1"},
            {"type": "length_difference", "lines": ["l1", "l0"], "value": 5.0}]
    r = SlvsSolver().solve(ents, cons, "sk")
    (ax, ay), (bx, by) = r.positions["a"], r.positions["b"]
    (cx, cy), (dx, dy) = r.positions["c"], r.positions["d"]
    assert math.isclose(math.hypot(dx - cx, dy - cy) - math.hypot(bx - ax, by - ay),
                        5.0, abs_tol=1e-3)


def test_equal_angle_matches_two_angle_pairs():
    ents = [
        {"id": "o", "type": "point", "at": [0, 0]},
        {"id": "a", "type": "point", "at": [10, 0]},
        {"id": "b", "type": "point", "at": [8, 5]},
        {"id": "c", "type": "point", "at": [7, 7]},
        {"id": "d", "type": "point", "at": [3, 9]},
        {"id": "l0", "type": "line", "p1": "o", "p2": "a"},
        {"id": "l1", "type": "line", "p1": "o", "p2": "b"},
        {"id": "l2", "type": "line", "p1": "o", "p2": "c"},
        {"id": "l3", "type": "line", "p1": "o", "p2": "d"},
    ]
    cons = [{"type": "fix", "of": "o"}, {"type": "fix", "of": "a"}, {"type": "fix", "of": "c"},
            {"type": "distance", "points": ["o", "b"], "value": 10},
            {"type": "distance", "points": ["o", "d"], "value": 10},
            {"type": "equal_angle", "lines": ["l0", "l1", "l2", "l3"]}]
    r = SlvsSolver().solve(ents, cons, "sk")
    assert r.status in ("well_constrained", "under_constrained")
    assert not any(i.level == "error" for i in r.issues)


def test_length_ratio_wrong_ref_count_is_error():
    ents = _two_lines()
    r = SlvsSolver().solve(ents, [{"type": "length_ratio", "lines": ["l0"], "value": 2}], "sk")
    assert r.status == "inconsistent"


def test_length_difference_missing_value_is_error():
    ents = _two_lines()
    r = SlvsSolver().solve(ents, [{"type": "length_difference", "lines": ["l0", "l1"]}], "sk")
    assert r.status == "inconsistent"


def test_well_constrained_has_no_failing_ids():
    entities = [
        {"id": "p0", "type": "point", "at": [0.0, 0.0]},
        {"id": "p1", "type": "point", "at": [10.0, 0.0]},
        {"id": "l", "type": "line", "p1": "p0", "p2": "p1"},
    ]
    constraints = [
        {"id": "fix0", "type": "fix", "of": "p0"},
        {"id": "fix1", "type": "fix", "of": "p1"},
    ]
    result = SlvsSolver().solve(entities, constraints, "sk")
    assert result.failing_ids == []
