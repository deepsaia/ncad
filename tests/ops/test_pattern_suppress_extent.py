from ncad.ops.pattern_params import pattern_kwargs
from ncad.ops.pattern_placements import PatternPlacements


def test_extent_divides_by_count_minus_one():
    kw = pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "extent": 30, "count": 4}})
    # extent 30 over 4 instances -> 3 gaps of 10.
    assert kw["linear"]["x"]["spacing"] == 10.0


def test_spacing_still_supported():
    kw = pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 5, "count": 3}})
    assert kw["linear"]["x"]["spacing"] == 5.0


def test_suppress_keeps_all_specs_for_the_op_to_drop():
    kw = pattern_kwargs({"kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 5, "count": 4},
                         "suppress": [1]})
    assert kw["suppress"] == [1]
    # PatternPlacements still generates all 4 ordinals; the op removes ordinal 1.
    specs = PatternPlacements(kw).specs()
    assert len(specs) == 4
