import pytest

from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_mirror_preserves_volume():
    k = FakeKernel()
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 0.0})
    assert k.volume(r) == pytest.approx(1000.0)


def test_mirror_across_yz_reflects_x_bounds():
    k = FakeKernel()
    # box spans x in [0, 10]; reflecting across YZ (x=0) -> x in [-10, 0]
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 0.0})
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(-10.0)
    assert maxx == pytest.approx(0.0)


def test_mirror_across_offset_yz_reflects_about_offset():
    k = FakeKernel()
    # box x in [0, 10]; reflect across x=15 -> x in [20, 30]
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 15.0})
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(20.0)
    assert maxx == pytest.approx(30.0)


def test_mirror_across_xz_reflects_y_bounds():
    k = FakeKernel()
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "XZ", "offset": 0.0})
    (_, miny, _), (_, maxy, _) = k.bounding_box(r)
    assert miny == pytest.approx(-10.0)
    assert maxy == pytest.approx(0.0)


def test_mirror_custom_plane_reflects_about_point_normal():
    k = FakeKernel()
    # plane through (15,0,0) with normal +X == the x=15 plane; box x in [0,10] -> [20,30]
    r = k.mirror(_box(k), plane={"kind": "custom", "point": (15.0, 0.0, 0.0),
                                 "z_dir": (1.0, 0.0, 0.0)})
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(20.0)
    assert maxx == pytest.approx(30.0)
