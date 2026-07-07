import pytest

from ncad.ops.draft_params import DraftParamError, draft_kwargs


def test_defaults_neutral_xy_offset_zero():
    kw = draft_kwargs({"angle": 5})
    assert kw == {"angle": 5.0, "neutral": "XY", "neutral_offset": 0.0}


def test_neutral_and_offset_parse():
    kw = draft_kwargs({"angle": 5, "neutral": "XZ", "neutral_offset": -10})
    assert kw["neutral"] == "XZ" and kw["neutral_offset"] == -10.0


def test_missing_angle_raises():
    with pytest.raises(DraftParamError, match="angle"):
        draft_kwargs({})


def test_angle_out_of_range_raises():
    with pytest.raises(DraftParamError, match="angle"):
        draft_kwargs({"angle": 0})
    with pytest.raises(DraftParamError, match="angle"):
        draft_kwargs({"angle": 90})


def test_bad_neutral_raises():
    with pytest.raises(DraftParamError, match="neutral"):
        draft_kwargs({"angle": 5, "neutral": "AB"})
