import pytest

from ncad.ops.pattern_params import PatternParamError, pattern_kwargs


def test_linear_1d_parses_with_defaults():
    kw = pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 20, "count": 4}})
    assert kw["kind"] == "linear"
    assert kw["merge"] is True  # default fuse
    assert kw["linear"]["x"] == {"dir": (1.0, 0.0, 0.0), "spacing": 20.0, "count": 4}
    assert kw["linear"]["y"] is None


def test_linear_2d_parses_both_axes_and_merge_false():
    kw = pattern_kwargs({"kind": "linear", "merge": False,
                         "x": {"dir": [1, 0, 0], "spacing": 20, "count": 4},
                         "y": {"dir": [0, 1, 0], "spacing": 15, "count": 3}})
    assert kw["merge"] is False
    assert kw["linear"]["y"] == {"dir": (0.0, 1.0, 0.0), "spacing": 15.0, "count": 3}


def test_circular_parses_with_axis_and_angle_defaults():
    kw = pattern_kwargs({"kind": "circular", "count": 6})
    c = kw["circular"]
    assert c["count"] == 6
    assert c["angle"] == 360.0     # default full circle
    assert c["rotate"] is True     # default follow the arc
    assert c["axis"]["point"] == (0.0, 0.0, 0.0)
    assert c["axis"]["dir"] == (0.0, 0.0, 1.0)  # default +Z


def test_circular_explicit_axis_and_partial_arc():
    kw = pattern_kwargs({"kind": "circular", "count": 4, "angle": 180, "rotate": False,
                         "axis": {"point": [1, 2, 3], "dir": [0, 1, 0]}})
    c = kw["circular"]
    assert c["angle"] == 180.0 and c["rotate"] is False
    assert c["axis"]["point"] == (1.0, 2.0, 3.0) and c["axis"]["dir"] == (0.0, 1.0, 0.0)


def test_unknown_kind_raises():
    with pytest.raises(PatternParamError, match="kind"):
        pattern_kwargs({"kind": "spiral", "count": 3})


def test_missing_kind_raises():
    with pytest.raises(PatternParamError, match="kind"):
        pattern_kwargs({"count": 3})


def test_linear_missing_x_raises():
    with pytest.raises(PatternParamError, match="x"):
        pattern_kwargs({"kind": "linear"})


def test_count_below_one_raises():
    with pytest.raises(PatternParamError, match="count"):
        pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 10, "count": 0}})
    with pytest.raises(PatternParamError, match="count"):
        pattern_kwargs({"kind": "circular", "count": 0})


def test_zero_spacing_raises():
    with pytest.raises(PatternParamError, match="spacing"):
        pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 0, "count": 3}})


def test_zero_direction_raises():
    with pytest.raises(PatternParamError, match="dir"):
        pattern_kwargs({"kind": "linear", "x": {"dir": [0, 0, 0], "spacing": 10, "count": 3}})


def test_zero_axis_dir_raises():
    with pytest.raises(PatternParamError, match="dir"):
        pattern_kwargs({"kind": "circular", "count": 3, "axis": {"dir": [0, 0, 0]}})


def test_non_positive_angle_raises():
    with pytest.raises(PatternParamError, match="angle"):
        pattern_kwargs({"kind": "circular", "count": 3, "angle": 0})
