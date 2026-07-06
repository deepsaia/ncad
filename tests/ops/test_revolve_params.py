import pytest

from ncad.ops.revolve_params import RevolveParamError, revolve_kwargs


def test_named_axis_y():
    kw = revolve_kwargs({"axis": "Y"}, {})
    assert kw["axis_point"] == (0.0, 0.0, 0.0)
    assert kw["axis_dir"] == (0.0, 1.0, 0.0)
    assert kw["angle"] == 360.0 and kw["symmetric"] is False


def test_named_axis_x_and_z():
    assert revolve_kwargs({"axis": "X"}, {})["axis_dir"] == (1.0, 0.0, 0.0)
    assert revolve_kwargs({"axis": "Z"}, {})["axis_dir"] == (0.0, 0.0, 1.0)


def test_arbitrary_axis_point_dir_normalized():
    kw = revolve_kwargs({"axis": {"point": [10, 0, 0], "dir": [0, 0, 3]}}, {})
    assert kw["axis_point"] == (10.0, 0.0, 0.0)
    assert kw["axis_dir"] == (0.0, 0.0, 1.0)


def test_partial_angle_and_symmetric():
    kw = revolve_kwargs({"axis": "Y", "angle": 90, "symmetric": True}, {})
    assert kw["angle"] == 90.0 and kw["symmetric"] is True


def test_thin():
    assert revolve_kwargs({"axis": "Y", "thin": 2}, {})["thin"] == 2.0


def test_missing_axis_raises():
    with pytest.raises(RevolveParamError, match="axis"):
        revolve_kwargs({}, {})


def test_unknown_axis_keyword_raises():
    with pytest.raises(RevolveParamError, match="axis"):
        revolve_kwargs({"axis": "W"}, {})


def test_axis_reference_string_deferred():
    with pytest.raises(RevolveParamError, match="not yet supported"):
        revolve_kwargs({"axis": "datums.spin"}, {})


def test_zero_dir_raises():
    with pytest.raises(RevolveParamError, match="dir"):
        revolve_kwargs({"axis": {"point": [0, 0, 0], "dir": [0, 0, 0]}}, {})


def test_angle_out_of_range_raises():
    with pytest.raises(RevolveParamError, match="angle"):
        revolve_kwargs({"axis": "Y", "angle": 0}, {})
    with pytest.raises(RevolveParamError, match="angle"):
        revolve_kwargs({"axis": "Y", "angle": 400}, {})


def test_non_positive_thin_raises():
    with pytest.raises(RevolveParamError, match="thin"):
        revolve_kwargs({"axis": "Y", "thin": 0}, {})
