from ncad.sketch.geometry_intersector import GeometryIntersector


def _pts(**kw):
    return {k: (float(v[0]), float(v[1])) for k, v in kw.items()}


def test_line_line_crossing():
    a = {"type": "line", "p1": "a0", "p2": "a1"}
    b = {"type": "line", "p1": "b0", "p2": "b1"}
    seeds = _pts(a0=(-5, 0), a1=(5, 0), b0=(0, -5), b1=(0, 5))
    hits = GeometryIntersector().intersect(a, b, seeds)
    assert len(hits) == 1
    assert (round(hits[0][0], 6), round(hits[0][1], 6)) == (0.0, 0.0)


def test_parallel_lines_have_no_intersection():
    a = {"type": "line", "p1": "a0", "p2": "a1"}
    b = {"type": "line", "p1": "b0", "p2": "b1"}
    seeds = _pts(a0=(0, 0), a1=(10, 0), b0=(0, 3), b1=(10, 3))
    assert GeometryIntersector().intersect(a, b, seeds) == []


def test_line_circle_two_points():
    line = {"type": "line", "p1": "l0", "p2": "l1"}
    circle = {"type": "circle", "center": "c", "radius": 5.0}
    seeds = _pts(l0=(-10, 0), l1=(10, 0), c=(0, 0))
    hits = GeometryIntersector().intersect(line, circle, seeds)
    xs = sorted(round(h[0], 6) for h in hits)
    assert xs == [-5.0, 5.0]


def test_line_circle_tangent_one_point():
    line = {"type": "line", "p1": "l0", "p2": "l1"}
    circle = {"type": "circle", "center": "c", "radius": 5.0}
    seeds = _pts(l0=(-10, 5), l1=(10, 5), c=(0, 0))
    hits = GeometryIntersector().intersect(line, circle, seeds)
    assert len(hits) == 1
    assert (round(hits[0][0], 6), round(hits[0][1], 6)) == (0.0, 5.0)


def test_line_circle_miss():
    line = {"type": "line", "p1": "l0", "p2": "l1"}
    circle = {"type": "circle", "center": "c", "radius": 5.0}
    seeds = _pts(l0=(-10, 8), l1=(10, 8), c=(0, 0))
    assert GeometryIntersector().intersect(line, circle, seeds) == []


def test_intersections_are_ordered():
    line = {"type": "line", "p1": "l0", "p2": "l1"}
    circle = {"type": "circle", "center": "c", "radius": 5.0}
    seeds = _pts(l0=(10, 0), l1=(-10, 0), c=(0, 0))  # line authored right-to-left
    hits = GeometryIntersector().intersect(line, circle, seeds)
    # regardless of authored direction, results sort by x then y
    assert hits == sorted(hits)


def test_circle_circle_two_points():
    a = {"type": "circle", "center": "ca", "radius": 5.0}
    b = {"type": "circle", "center": "cb", "radius": 5.0}
    seeds = _pts(ca=(0, 0), cb=(8, 0))
    hits = GeometryIntersector().intersect(a, b, seeds)
    assert len(hits) == 2
    xs = {round(h[0], 6) for h in hits}
    assert xs == {4.0}
    ys = sorted(round(h[1], 6) for h in hits)
    assert ys == [-3.0, 3.0]


def test_circle_circle_separate_no_hit():
    a = {"type": "circle", "center": "ca", "radius": 2.0}
    b = {"type": "circle", "center": "cb", "radius": 2.0}
    seeds = _pts(ca=(0, 0), cb=(10, 0))
    assert GeometryIntersector().intersect(a, b, seeds) == []


def test_arc_range_filters_intersection():
    # a line crossing a circle at x=-5 and x=5, but the arc only spans the right half
    line = {"type": "line", "p1": "l0", "p2": "l1"}
    arc = {"type": "arc", "center": "c", "start": "s", "end": "e"}
    seeds = _pts(l0=(-10, 0), l1=(10, 0), c=(0, 0), s=(0, -5), e=(0, 5))
    hits = GeometryIntersector().intersect(line, arc, seeds)
    # CCW from (0,-5) to (0,5) sweeps the right half (through (5,0)), so only x=5 survives
    assert len(hits) == 1
    assert round(hits[0][0], 6) == 5.0
