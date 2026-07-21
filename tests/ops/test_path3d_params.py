"""path3d_kwargs validates points, kind, and closed; rejects malformed paths."""

import pytest

from ncad.ops.path3d_params import Path3dParamError, path3d_kwargs


def test_polyline_defaults():
    kwargs = path3d_kwargs({"points": [[0, 0, 0], [10, 0, 5]]})
    assert kwargs["kind"] == "polyline"
    assert kwargs["closed"] is False
    assert kwargs["points"] == [(0.0, 0.0, 0.0), (10.0, 0.0, 5.0)]


def test_spline_kind_and_closed():
    kwargs = path3d_kwargs(
        {"points": [[0, 0, 0], [10, 0, 5], [10, 10, 10]], "kind": "spline", "closed": True})
    assert kwargs["kind"] == "spline"
    assert kwargs["closed"] is True


def test_unknown_kind_raises():
    with pytest.raises(Path3dParamError, match="unknown path3d kind"):
        path3d_kwargs({"points": [[0, 0, 0], [1, 1, 1]], "kind": "arc3d"})


def test_too_few_points_raises():
    with pytest.raises(Path3dParamError, match="at least 2"):
        path3d_kwargs({"points": [[0, 0, 0]]})


def test_bad_point_shape_raises():
    with pytest.raises(Path3dParamError, match=r"\[x, y, z\]"):
        path3d_kwargs({"points": [[0, 0, 0], [1, 1]]})


def test_spline_needs_three_points():
    with pytest.raises(Path3dParamError, match="spline needs at least 3"):
        path3d_kwargs({"points": [[0, 0, 0], [1, 1, 1]], "kind": "spline"})
