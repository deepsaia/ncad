import pytest

from ncad.ops.chamfer_params import ChamferParamError, chamfer_kwargs


def test_symmetric_defaults():
    kw = chamfer_kwargs({"distance": 3})
    assert kw == {"distance": 3.0, "distance2": None, "angle": None}


def test_two_distance_parse():
    kw = chamfer_kwargs({"distance": 3, "distance2": 6})
    assert kw["distance"] == 3.0 and kw["distance2"] == 6.0 and kw["angle"] is None


def test_distance_angle_parse():
    kw = chamfer_kwargs({"distance": 3, "angle": 30})
    assert kw["angle"] == 30.0 and kw["distance2"] is None


def test_both_distance2_and_angle_raises():
    with pytest.raises(ChamferParamError, match="both"):
        chamfer_kwargs({"distance": 3, "distance2": 6, "angle": 30})


def test_missing_distance_raises():
    with pytest.raises(ChamferParamError, match="distance"):
        chamfer_kwargs({})


def test_nonpositive_distance_raises():
    with pytest.raises(ChamferParamError, match="distance"):
        chamfer_kwargs({"distance": 0})


def test_nonpositive_distance2_raises():
    with pytest.raises(ChamferParamError, match="distance2"):
        chamfer_kwargs({"distance": 3, "distance2": -1})


def test_angle_out_of_range_raises():
    with pytest.raises(ChamferParamError, match="angle"):
        chamfer_kwargs({"distance": 3, "angle": 0})
    with pytest.raises(ChamferParamError, match="angle"):
        chamfer_kwargs({"distance": 3, "angle": 90})
