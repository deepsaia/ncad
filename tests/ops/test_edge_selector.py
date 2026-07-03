import pytest

from ncad.ops.edge_selector import EdgeSelector


def _infos():
    return [
        {"edge": "v1", "orientation": "vertical", "mid_z": 4.0},
        {"edge": "v2", "orientation": "vertical", "mid_z": 4.0},
        {"edge": "t1", "orientation": "horizontal", "mid_z": 8.0},
        {"edge": "b1", "orientation": "horizontal", "mid_z": 0.0},
    ]


def test_all() -> None:
    assert set(EdgeSelector().select(_infos(), "all")) == {"v1", "v2", "t1", "b1"}


def test_vertical() -> None:
    assert set(EdgeSelector().select(_infos(), "vertical")) == {"v1", "v2"}


def test_horizontal() -> None:
    assert set(EdgeSelector().select(_infos(), "horizontal")) == {"t1", "b1"}


def test_top_and_bottom() -> None:
    assert EdgeSelector().select(_infos(), "top") == ["t1"]
    assert EdgeSelector().select(_infos(), "bottom") == ["b1"]


def test_unknown_keyword_raises() -> None:
    with pytest.raises(ValueError):
        EdgeSelector().select(_infos(), "diagonal")
