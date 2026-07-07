import pytest

from ncad.ops.loft_params import LoftParamError, loft_kwargs


def test_ruled_defaults_false():
    kw = loft_kwargs({}, {"sections": [object(), object()]})
    assert kw["ruled"] is False
    assert kw["start_point"] is None and kw["end_point"] is None


def test_ruled_true_and_points_parse():
    kw = loft_kwargs(
        {"ruled": True, "start_point": [0, 0, -5], "end_point": [0, 0, 10]},
        {"sections": [object()]})
    assert kw["ruled"] is True
    assert kw["start_point"] == (0.0, 0.0, -5.0)
    assert kw["end_point"] == (0.0, 0.0, 10.0)


def test_bad_point_length_raises():
    with pytest.raises(LoftParamError, match="point"):
        loft_kwargs({"start_point": [0, 0]}, {"sections": [object(), object()]})


def test_section_count_under_two_raises():
    with pytest.raises(LoftParamError, match="at least 2"):
        loft_kwargs({}, {"sections": [object()]})


def test_one_section_plus_point_cap_is_enough():
    kw = loft_kwargs({"end_point": [0, 0, 5]}, {"sections": [object()]})
    assert kw["end_point"] == (0.0, 0.0, 5.0)
