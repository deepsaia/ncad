import pytest

from ncad.ops.plane_spec import PlaneSpecError, parse_plane


def test_base_plane_with_offset():
    assert parse_plane("YZ", 0) == {"kind": "base", "plane": "YZ", "offset": 0.0}
    assert parse_plane("XZ", 12) == {"kind": "base", "plane": "XZ", "offset": 12.0}


def test_custom_plane_maps_normal_to_z_dir():
    assert parse_plane({"point": [1, 2, 3], "normal": [1, 0, 0]}, 0) == {
        "kind": "custom", "point": (1.0, 2.0, 3.0), "z_dir": (1.0, 0.0, 0.0)}


def test_custom_plane_default_point_origin():
    p = parse_plane({"normal": [0, 1, 0]}, 0)
    assert p["point"] == (0.0, 0.0, 0.0) and p["z_dir"] == (0.0, 1.0, 0.0)


def test_unknown_base_plane_raises():
    with pytest.raises(PlaneSpecError, match="plane"):
        parse_plane("AB", 0)


def test_zero_normal_raises():
    with pytest.raises(PlaneSpecError, match="normal"):
        parse_plane({"normal": [0, 0, 0]}, 0)


def test_missing_normal_raises():
    with pytest.raises(PlaneSpecError, match="normal"):
        parse_plane({"point": [0, 0, 0]}, 0)


def test_bad_type_raises():
    with pytest.raises(PlaneSpecError, match="plane"):
        parse_plane(42, 0)
