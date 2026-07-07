import pytest

from ncad.ops.hole_params import HoleParamError, hole_kwargs


def test_explicit_diameter_wins():
    kw = hole_kwargs({"diameter": 6, "size": "M8", "fit": "normal"})
    assert kw["diameter"] == 6.0


def test_size_and_fit_resolve_diameter():
    kw = hole_kwargs({"size": "M6", "fit": "normal"})
    assert kw["diameter"] == 6.6


def test_missing_size_and_diameter_raises():
    with pytest.raises(HoleParamError, match="diameter"):
        hole_kwargs({})


def test_counterbore_parses():
    kw = hole_kwargs({"diameter": 6, "counterbore": {"diameter": 12, "depth": 5}})
    assert kw["counterbore"] == {"diameter": 12.0, "depth": 5.0}
    assert kw["countersink"] is None


def test_countersink_parses_with_default_angle():
    kw = hole_kwargs({"diameter": 6, "countersink": {"diameter": 12}})
    assert kw["countersink"]["diameter"] == 12.0
    assert kw["countersink"]["angle"] == 82.0


def test_both_counterbore_and_countersink_raises():
    with pytest.raises(HoleParamError, match="both"):
        hole_kwargs({"diameter": 6, "counterbore": {"diameter": 12, "depth": 5},
                     "countersink": {"diameter": 12}})


def test_thread_tag_passthrough():
    kw = hole_kwargs({"size": "M6", "fit": "tapped", "thread": "M6"})
    assert kw["thread"] == "M6"


def test_nonpositive_diameter_raises():
    with pytest.raises(HoleParamError, match="diameter"):
        hole_kwargs({"diameter": 0})
