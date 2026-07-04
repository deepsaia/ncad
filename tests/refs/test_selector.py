import pytest

from ncad.refs.selector import Selector
from ncad.refs.selector_error import SelectorError


class _E:
    def __init__(self, kind, **attrs):
        self.kind = kind
        self.attrs = {"kind": kind, **attrs}


def _elements():
    return [
        _E("edge", created_by="pad", orientation="vertical", length=10.0, mid_z=5.0),
        _E("edge", created_by="pad", orientation="horizontal", length=20.0, mid_z=0.0),
        _E("edge", created_by="hole", orientation="vertical", length=8.0, mid_z=4.0),
        _E("face", created_by="pad", area=200.0, normal_z=1.0),
    ]


def test_select_edges_by_created_by_and_orientation():
    got = Selector().select(
        "select edges where created_by='pad' and orientation='vertical'", _elements())
    assert len(got) == 1 and got[0].attrs["length"] == 10.0


def test_select_faces_only_returns_faces():
    got = Selector().select("select faces where created_by='pad'", _elements())
    assert len(got) == 1 and got[0].kind == "face"


def test_or_and_numeric_comparison():
    got = Selector().select(
        "select edges where length>15 or created_by='hole'", _elements())
    assert {round(e.attrs["length"]) for e in got} == {20, 8}


def test_parentheses_group_predicate():
    got = Selector().select(
        "select edges where orientation='vertical' and (created_by='pad' or created_by='hole')",
        _elements())
    assert len(got) == 2


def test_unknown_attribute_raises():
    with pytest.raises(SelectorError):
        Selector().select("select edges where convexity='convex'", _elements())


def test_bad_syntax_raises():
    with pytest.raises(SelectorError):
        Selector().select("select edges where and or", _elements())


def test_missing_select_keyword_raises():
    with pytest.raises(SelectorError):
        Selector().select("edges where created_by='pad'", _elements())
