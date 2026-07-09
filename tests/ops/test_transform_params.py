import pytest

from ncad.ops.transform_params import TransformParamError, transform_kwargs


def test_move_parses():
    kw = transform_kwargs({"move": [20, 0, 0]})
    assert kw["move"] == (20.0, 0.0, 0.0) and kw["copy"] is False


def test_rotate_parses_axis_angle_about_default_origin():
    kw = transform_kwargs({"rotate": {"axis": "Z", "angle": 45}})
    assert kw["rotate"]["axis"] == (0.0, 0.0, 1.0)
    assert kw["rotate"]["angle"] == 45.0
    assert kw["rotate"]["about"] == (0.0, 0.0, 0.0)


def test_rotate_about_point_and_vector_axis():
    kw = transform_kwargs({"rotate": {"axis": [1, 0, 0], "angle": 90, "about": [5, 0, 0]}})
    assert kw["rotate"]["axis"] == (1.0, 0.0, 0.0) and kw["rotate"]["about"] == (5.0, 0.0, 0.0)


def test_uniform_and_non_uniform_scale():
    assert transform_kwargs({"scale": 2})["scale"] == 2.0
    assert transform_kwargs({"scale": [2, 1, 0.5]})["scale"] == (2.0, 1.0, 0.5)


def test_copy_flag():
    assert transform_kwargs({"move": [1, 0, 0], "copy": True})["copy"] is True


def test_no_transform_given_raises():
    with pytest.raises(TransformParamError, match="move.*rotate.*scale"):
        transform_kwargs({})


def test_zero_scale_raises():
    with pytest.raises(TransformParamError, match="scale"):
        transform_kwargs({"scale": 0})
    with pytest.raises(TransformParamError, match="scale"):
        transform_kwargs({"scale": [1, 0, 1]})


def test_bad_rotate_axis_raises():
    with pytest.raises(TransformParamError, match="axis"):
        transform_kwargs({"rotate": {"axis": "W", "angle": 10}})
