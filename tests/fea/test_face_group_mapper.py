import pytest

from ncad.fea.face_group_mapper import FaceGroupError, FaceGroupMapper

# A minimal box-like surface set: bottom (z=0, -z normal), top (z=6, +z normal),
# and three verticals; tags mimic gmsh's own numbering.
_SURFACES = [
    {"tag": 1, "com": (0, 0, 0), "normal": (0, 0, -1), "zmin": 0, "zmax": 0, "area": 100.0},
    {"tag": 2, "com": (0, 0, 6), "normal": (0, 0, 1), "zmin": 6, "zmax": 6, "area": 100.0},
    {"tag": 3, "com": (-5, 0, 3), "normal": (-1, 0, 0), "zmin": 0, "zmax": 6, "area": 60.0},
    {"tag": 4, "com": (5, 0, 3), "normal": (1, 0, 0), "zmin": 0, "zmax": 6, "area": 60.0},
    {"tag": 5, "com": (0, -5, 3), "normal": (0, -1, 0), "zmin": 0, "zmax": 6, "area": 60.0},
]


def test_all_selects_every_surface():
    assert set(FaceGroupMapper().select(_SURFACES, {"face": "all"})) == {1, 2, 3, 4, 5}


def test_bottom_selects_lowest_horizontal():
    assert FaceGroupMapper().select(_SURFACES, {"face": "bottom"}) == [1]


def test_top_selects_highest_horizontal():
    assert FaceGroupMapper().select(_SURFACES, {"face": "top"}) == [2]


def test_vertical_selects_side_faces():
    assert set(FaceGroupMapper().select(_SURFACES, {"face": "vertical"})) == {3, 4, 5}


def test_horizontal_selects_caps():
    assert set(FaceGroupMapper().select(_SURFACES, {"face": "horizontal"})) == {1, 2}


def test_unknown_keyword_raises():
    with pytest.raises(FaceGroupError):
        FaceGroupMapper().select(_SURFACES, {"face": "diagonal"})


def test_missing_face_key_raises():
    with pytest.raises(FaceGroupError):
        FaceGroupMapper().select(_SURFACES, {"plane": "z"})


def test_empty_match_raises():
    # No horizontal surfaces -> top/bottom must be a loud failure, not a silent empty set.
    verticals_only = [s for s in _SURFACES if s["tag"] in (3, 4, 5)]
    with pytest.raises(FaceGroupError):
        FaceGroupMapper().select(verticals_only, {"face": "top"})
