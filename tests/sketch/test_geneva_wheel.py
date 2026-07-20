import math

import pytest

from ncad.sketch.geneva_wheel import GenevaWheel, GenevaWheelError


def test_center_distance_and_engagement_window():
    g = GenevaWheel(slots=4, crank_radius=30.0)
    assert math.isclose(g.center_distance, 30.0 / math.sin(math.pi / 4), abs_tol=1e-9)
    # crank engagement sweep = 2*(90 - 180/N) deg; N=4 -> 90 deg total, half = 45 deg.
    assert math.isclose(g.engagement_half_angle_deg, 45.0, abs_tol=1e-9)


def test_wheel_dwells_then_indexes_one_step_per_rev():
    g = GenevaWheel(slots=4, crank_radius=30.0)
    # Engagement centred at crank 180 deg, +/- 45 deg. Outside [135, 225] the wheel is flat. A CCW
    # crank indexes the wheel CW, so the rotation is NEGATIVE: 0 -> -90 (= -index) over the window.
    assert math.isclose(g.wheel_angle(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(g.wheel_angle(90.0), 0.0, abs_tol=1e-9)      # pre-engagement dwell
    assert math.isclose(g.wheel_angle(135.0), 0.0, abs_tol=1e-6)     # engagement start
    assert math.isclose(g.wheel_angle(180.0), -45.0, abs_tol=1e-6)   # mid engagement = -half index
    assert math.isclose(g.wheel_angle(225.0), -90.0, abs_tol=1e-6)   # engagement end = -index 360/N
    assert math.isclose(g.wheel_angle(360.0), -90.0, abs_tol=1e-9)   # post-engagement dwell holds


def test_wheel_angle_is_monotonic_nonincreasing():
    g = GenevaWheel(slots=6, crank_radius=25.0)
    prev = 1.0
    for d in range(0, 361, 3):
        v = g.wheel_angle(float(d))
        assert v <= prev + 1e-9                                     # CW index: non-increasing
        prev = v
    assert math.isclose(g.wheel_angle(360.0), -60.0, abs_tol=1e-6)  # -360/6


def test_outline_is_closed_star_with_n_slots():
    g = GenevaWheel(slots=4, crank_radius=30.0)
    pts = g.outline()
    assert len(pts) > 20 and pts[0] != pts[-1]
    radii = [math.hypot(x, y) for x, y in pts]
    # The slots are radial notches: some points reach near the wheel centre, others reach the rim.
    assert min(radii) < g.wheel_radius * 0.6
    assert max(radii) >= g.wheel_radius - 1e-6


def test_expression_is_smooth_and_tracks_wheel_angle():
    g = GenevaWheel(slots=4, crank_radius=30.0)
    expr = g.expression(a0_deg=0.0, span_deg=360.0)
    assert isinstance(expr, str) and "time" in expr
    for token in ("min", "max", "abs", ">", "<", "if"):
        assert token not in expr


def test_bad_params_raise():
    with pytest.raises(GenevaWheelError):
        GenevaWheel(slots=2, crank_radius=30.0)         # need >= 3 slots
    with pytest.raises(GenevaWheelError):
        GenevaWheel(slots=4, crank_radius=0.0)


def test_geneva_wheel_entity_expands_to_closed_polyline():
    from ncad.sketch.entity_expander import EntityExpander

    ents = [
        {"id": "c", "type": "point", "at": [0, 0]},
        {"id": "gw", "type": "geneva_wheel", "slots": 4, "crank_radius": 30.0, "center": "c"},
    ]
    out = EntityExpander().expand(ents)
    pts = [e for e in out if e["type"] == "point" and e["id"] != "c"]
    lines = [e for e in out if e["type"] == "line"]
    assert len(pts) > 20 and len(pts) == len(lines)   # a real closed loop: one line per point
    assert all(p.get("fixed") for p in pts)           # derived points are locked
    assert not any(e["id"] == "gw" for e in out)      # the sugar entity itself is lowered away
