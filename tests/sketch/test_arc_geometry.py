import math

from ncad.sketch.arc_geometry import arc_contains, seed_radius


def test_seed_radius_explicit_circle():
    assert seed_radius({"type": "circle", "center": "c", "radius": 7.0}, {}) == 7.0


def test_seed_radius_arc_from_seeds():
    seeds = {"c": (0.0, 0.0), "s": (5.0, 0.0)}
    arc = {"type": "arc", "center": "c", "start": "s", "end": "e"}
    assert seed_radius(arc, seeds) == 5.0


def _quarter_arc():
    # CCW quarter arc from (5,0) to (0,5) about the origin: sweeps the first quadrant
    seeds = {"c": (0.0, 0.0), "s": (5.0, 0.0), "e": (0.0, 5.0)}
    arc = {"type": "arc", "center": "c", "start": "s", "end": "e"}
    return arc, seeds


def test_arc_contains_interior_point():
    arc, seeds = _quarter_arc()
    mid = (5.0 * math.cos(math.pi / 4), 5.0 * math.sin(math.pi / 4))
    assert arc_contains(arc, mid, seeds, inclusive=True)
    assert arc_contains(arc, mid, seeds, inclusive=False)


def test_arc_contains_excludes_point_outside_span():
    arc, seeds = _quarter_arc()
    outside = (5.0 * math.cos(-math.pi / 4), 5.0 * math.sin(-math.pi / 4))
    assert not arc_contains(arc, outside, seeds, inclusive=True)
    assert not arc_contains(arc, outside, seeds, inclusive=False)


def test_arc_contains_endpoint_inclusive_vs_exclusive():
    arc, seeds = _quarter_arc()
    start = (5.0, 0.0)
    assert arc_contains(arc, start, seeds, inclusive=True)
    assert not arc_contains(arc, start, seeds, inclusive=False)
