import pytest

from ncad.ops.primitive_params import PrimitiveParamError, primitive_kwargs


def test_box_dims():
    kw = primitive_kwargs({"kind": "box", "w": 40, "d": 30, "h": 10})
    assert kw["kind"] == "box"
    assert kw["dims"] == {"w": 40.0, "d": 30.0, "h": 10.0}
    assert kw["plane"] == "XY" and kw["at"] == (0.0, 0.0)


def test_cylinder_accepts_d_or_r():
    by_d = primitive_kwargs({"kind": "cylinder", "d": 20, "h": 50})
    by_r = primitive_kwargs({"kind": "cylinder", "r": 10, "h": 50})
    assert by_d["dims"]["radius"] == 10.0 and by_r["dims"]["radius"] == 10.0


def test_torus_and_cone_dims():
    t = primitive_kwargs({"kind": "torus", "major_d": 60, "minor_d": 8})
    assert t["dims"] == {"major_radius": 30.0, "minor_radius": 4.0}
    c = primitive_kwargs({"kind": "cone", "bottom_d": 20, "top_d": 0, "h": 25})
    assert c["dims"] == {"bottom_radius": 10.0, "top_radius": 0.0, "h": 25.0}


def test_plane_and_at_pass_through():
    kw = primitive_kwargs({"kind": "sphere", "d": 30, "plane": "XZ", "at": [5, 6]})
    assert kw["plane"] == "XZ" and kw["at"] == (5.0, 6.0)


def test_unknown_kind_raises():
    with pytest.raises(PrimitiveParamError):
        primitive_kwargs({"kind": "prism", "w": 1, "d": 1, "h": 1})


def test_missing_dimension_raises():
    with pytest.raises(PrimitiveParamError):
        primitive_kwargs({"kind": "box", "w": 40, "h": 10})  # missing d
