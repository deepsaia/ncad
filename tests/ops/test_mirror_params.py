import pytest

from ncad.ops.mirror_params import MirrorParamError, mirror_kwargs


def test_base_plane_defaults():
    kw = mirror_kwargs({"plane": "YZ"})
    assert kw["plane"] == {"kind": "base", "plane": "YZ", "offset": 0.0}
    assert kw["keep"] is True   # default keep original + add reflection
    assert kw["merge"] is True  # default fuse to one solid


def test_base_plane_with_offset_and_flags():
    kw = mirror_kwargs({"plane": "XZ", "plane_offset": 12, "keep": False, "merge": False})
    assert kw["plane"] == {"kind": "base", "plane": "XZ", "offset": 12.0}
    assert kw["keep"] is False and kw["merge"] is False


def test_custom_plane_maps_normal_to_z_dir():
    kw = mirror_kwargs({"plane": {"point": [1, 2, 3], "normal": [1, 0, 0]}})
    assert kw["plane"] == {"kind": "custom", "point": (1.0, 2.0, 3.0),
                           "z_dir": (1.0, 0.0, 0.0)}


def test_custom_plane_default_point_origin():
    kw = mirror_kwargs({"plane": {"normal": [0, 1, 0]}})
    assert kw["plane"]["point"] == (0.0, 0.0, 0.0)
    assert kw["plane"]["z_dir"] == (0.0, 1.0, 0.0)


def test_unknown_base_plane_raises():
    with pytest.raises(MirrorParamError, match="plane"):
        mirror_kwargs({"plane": "AB"})


def test_missing_plane_raises():
    with pytest.raises(MirrorParamError, match="plane"):
        mirror_kwargs({})


def test_custom_plane_zero_normal_raises():
    with pytest.raises(MirrorParamError, match="normal"):
        mirror_kwargs({"plane": {"point": [0, 0, 0], "normal": [0, 0, 0]}})


def test_custom_plane_missing_normal_raises():
    with pytest.raises(MirrorParamError, match="normal"):
        mirror_kwargs({"plane": {"point": [0, 0, 0]}})
