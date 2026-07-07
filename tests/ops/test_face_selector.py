import pytest

from ncad.ops.face_selector import FaceSelector


def _faces():
    # A box: top (+Z), bottom (-Z), and four vertical sides (normal Z ~ 0).
    return [
        {"handle": "top", "normal": (0.0, 0.0, 1.0), "mid_z": 10.0},
        {"handle": "bottom", "normal": (0.0, 0.0, -1.0), "mid_z": 0.0},
        {"handle": "s1", "normal": (1.0, 0.0, 0.0), "mid_z": 5.0},
        {"handle": "s2", "normal": (-1.0, 0.0, 0.0), "mid_z": 5.0},
        {"handle": "s3", "normal": (0.0, 1.0, 0.0), "mid_z": 5.0},
        {"handle": "s4", "normal": (0.0, -1.0, 0.0), "mid_z": 5.0},
    ]


def test_all_selects_every_face():
    assert len(FaceSelector().select(_faces(), "all")) == 6


def test_top_selects_highest_mid_z():
    assert FaceSelector().select(_faces(), "top") == ["top"]


def test_bottom_selects_lowest_mid_z():
    assert FaceSelector().select(_faces(), "bottom") == ["bottom"]


def test_vertical_selects_side_faces():
    handles = FaceSelector().select(_faces(), "vertical")
    assert set(handles) == {"s1", "s2", "s3", "s4"}


def test_horizontal_selects_caps():
    handles = FaceSelector().select(_faces(), "horizontal")
    assert set(handles) == {"top", "bottom"}


def test_unknown_keyword_raises():
    with pytest.raises(ValueError, match="face keyword"):
        FaceSelector().select(_faces(), "sideways")
