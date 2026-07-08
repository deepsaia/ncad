import pytest

from ncad.ops.wrap_params import WrapParamError, wrap_kwargs


def test_text_defaults():
    kw = wrap_kwargs({"text": "AB", "depth": 1})
    assert kw["text"] == "AB" and kw["depth"] == 1.0
    assert kw["font_size"] == 5.0 and kw["mode"] == "emboss"
    assert kw["offset"] == (0.0, 0.0) and kw["rotation"] == 0.0


def test_offset_rotation_mode_parse():
    kw = wrap_kwargs({"text": "AB", "depth": 1, "mode": "engrave",
                      "offset": [10, -3], "rotation": 90})
    assert kw["mode"] == "engrave" and kw["offset"] == (10.0, -3.0)
    assert kw["rotation"] == 90.0


def test_missing_depth_raises():
    with pytest.raises(WrapParamError, match="depth"):
        wrap_kwargs({"text": "AB"})


def test_nonpositive_depth_raises():
    with pytest.raises(WrapParamError, match="depth"):
        wrap_kwargs({"text": "AB", "depth": 0})


def test_bad_mode_raises():
    with pytest.raises(WrapParamError, match="mode"):
        wrap_kwargs({"text": "AB", "depth": 1, "mode": "raise"})


def test_bad_offset_raises():
    with pytest.raises(WrapParamError, match="offset"):
        wrap_kwargs({"text": "AB", "depth": 1, "offset": [1, 2, 3]})


def test_profile_source_has_no_text():
    kw = wrap_kwargs({"depth": 1})  # profile-only: text absent, resolved by the op
    assert kw["text"] is None
