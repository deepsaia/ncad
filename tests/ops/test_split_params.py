import pytest

from ncad.ops.split_params import SplitParamError, split_kwargs


def test_base_plane_default_keep_both():
    kw = split_kwargs({"plane": "XY"})
    assert kw["plane"] == {"kind": "base", "plane": "XY", "offset": 0.0}
    assert kw["keep"] == "both"


def test_offset_and_keep_top():
    kw = split_kwargs({"plane": "YZ", "plane_offset": 5, "keep": "top"})
    assert kw["plane"]["offset"] == 5.0 and kw["keep"] == "top"


def test_custom_plane():
    kw = split_kwargs({"plane": {"point": [0, 0, 0], "normal": [0, 0, 1]}})
    assert kw["plane"]["kind"] == "custom"


def test_missing_plane_raises():
    with pytest.raises(SplitParamError, match="plane"):
        split_kwargs({})


def test_unknown_keep_raises():
    with pytest.raises(SplitParamError, match="keep"):
        split_kwargs({"plane": "XY", "keep": "middle"})


def test_bad_plane_raises():
    with pytest.raises(SplitParamError, match="plane"):
        split_kwargs({"plane": "AB"})
