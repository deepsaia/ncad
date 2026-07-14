import pytest

from ncad.ops.mirror_params import MirrorParamError, mirror_kwargs


class _FakePlanarFace:
    def __init__(self, center, normal, planar=True):
        self._c, self._n = center, normal
        self.geom_type = "PLANE" if planar else "CYLINDER"

    def center(self):
        return type("V", (), {"X": self._c[0], "Y": self._c[1], "Z": self._c[2]})()

    def normal_at(self, *_args):
        return type("V", (), {"X": self._n[0], "Y": self._n[1], "Z": self._n[2]})()


def test_plane_string_unchanged():
    kw = mirror_kwargs({"plane": "XY"}, {})
    assert kw["plane"]["kind"] == "base" and kw["plane"]["plane"] == "XY"


def test_mirror_face_ref_becomes_custom_plane():
    face = _FakePlanarFace(center=(0, 0, 5), normal=(0, 0, 1))
    kw = mirror_kwargs({}, {"face": face})
    assert kw["plane"]["kind"] == "custom"
    assert kw["plane"]["point"] == (0.0, 0.0, 5.0)
    assert kw["plane"]["z_dir"] == (0.0, 0.0, 1.0)


def test_non_planar_face_refuses():
    face = _FakePlanarFace(center=(0, 0, 0), normal=(0, 0, 1), planar=False)
    with pytest.raises(MirrorParamError):
        mirror_kwargs({}, {"face": face})
