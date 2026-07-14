import pytest

from ncad.ops.pattern_params import PatternParamError, pattern_kwargs
from ncad.ops.pattern_placements import PatternPlacements


def test_table_one_spec_per_row():
    kw = pattern_kwargs({"kind": "table",
                         "placements": [{"at": [0, 0, 0]}, {"at": [10, 0, 0]},
                                        {"at": [10, 10, 0], "rotate": 90}]})
    specs = PatternPlacements(kw).specs()
    assert len(specs) == 3
    assert specs[0] == {}                       # origin, no rotate -> seed
    assert specs[1]["move"] == (10.0, 0.0, 0.0)
    assert specs[2]["move"] == (10.0, 10.0, 0.0)
    assert specs[2]["rotate"]["angle"] == 90.0
    assert specs[2]["rotate"]["about"] == (10.0, 10.0, 0.0)


def test_table_needs_placements():
    with pytest.raises(PatternParamError):
        pattern_kwargs({"kind": "table", "placements": []})


def test_table_row_needs_at():
    with pytest.raises(PatternParamError):
        pattern_kwargs({"kind": "table", "placements": [{"rotate": 30}]})
