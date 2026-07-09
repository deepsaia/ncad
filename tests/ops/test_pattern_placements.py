import pytest

from ncad.ops.pattern_params import pattern_kwargs
from ncad.ops.pattern_placements import PatternPlacements


def _linear(**kw):
    return pattern_kwargs({"kind": "linear", **kw})


def test_linear_1d_moves_along_dir_seed_is_identity():
    kw = _linear(x={"dir": [1, 0, 0], "spacing": 20, "count": 4})
    specs = PatternPlacements(kw).specs()
    assert len(specs) == 4
    assert specs[0] == {}  # seed = identity
    assert specs[1]["move"] == (20.0, 0.0, 0.0)
    assert specs[3]["move"] == (60.0, 0.0, 0.0)


def test_linear_2d_row_major_ordinals():
    kw = _linear(x={"dir": [1, 0, 0], "spacing": 20, "count": 2},
                 y={"dir": [0, 1, 0], "spacing": 15, "count": 2})
    specs = PatternPlacements(kw).specs()
    assert len(specs) == 4
    assert specs[0] == {}                          # ix=0, iy=0
    assert specs[1]["move"] == (20.0, 0.0, 0.0)    # ix=1, iy=0
    assert specs[2]["move"] == (0.0, 15.0, 0.0)    # ix=0, iy=1
    assert specs[3]["move"] == (20.0, 15.0, 0.0)   # ix=1, iy=1


def test_circular_full_rotate_true_steps_60_degrees():
    kw = pattern_kwargs({"kind": "circular", "count": 6})
    specs = PatternPlacements(kw).specs()
    assert len(specs) == 6
    assert specs[0] == {}
    assert specs[1]["rotate"]["angle"] == pytest.approx(60.0)
    assert specs[1]["rotate"]["axis"] == (0.0, 0.0, 1.0)
    assert specs[1]["rotate"]["about"] == (0.0, 0.0, 0.0)
    assert specs[5]["rotate"]["angle"] == pytest.approx(300.0)


def test_circular_partial_arc_hits_both_ends():
    kw = pattern_kwargs({"kind": "circular", "count": 4, "angle": 180})
    specs = PatternPlacements(kw).specs()
    # angle/(count-1) = 180/3 = 60 -> 0, 60, 120, 180
    assert specs[3]["rotate"]["angle"] == pytest.approx(180.0)


def test_circular_rotate_false_translates_anchor_around_axis():
    kw = pattern_kwargs({"kind": "circular", "count": 4, "rotate": False})
    # anchor at (10,0,0); a 90-degree step about +Z through origin -> (0,10,0); move = (-10,10,0)
    specs = PatternPlacements(kw, anchor=(10.0, 0.0, 0.0)).specs()
    assert specs[0] == {}
    dx, dy, dz = specs[1]["move"]
    assert dx == pytest.approx(-10.0, abs=1e-9)
    assert dy == pytest.approx(10.0, abs=1e-9)
    assert dz == pytest.approx(0.0, abs=1e-9)
    assert "rotate" not in specs[1]


def test_circular_rotate_false_without_anchor_raises():
    kw = pattern_kwargs({"kind": "circular", "count": 3, "rotate": False})
    with pytest.raises(ValueError, match="anchor"):
        PatternPlacements(kw).specs()


def test_count_one_yields_only_seed():
    kw = _linear(x={"dir": [1, 0, 0], "spacing": 20, "count": 1})
    assert PatternPlacements(kw).specs() == [{}]
