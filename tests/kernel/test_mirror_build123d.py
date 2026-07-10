import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_mirror_preserves_volume_and_validity():
    k = _kernel()
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 0.0})
    assert k.volume(r) == pytest.approx(1000.0, rel=1e-6)


def test_mirror_across_yz_reflects_x_bounds():
    k = _kernel()
    r = k.mirror(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 0.0})
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(-10.0, abs=1e-6)
    assert maxx == pytest.approx(0.0, abs=1e-6)


def test_mirror_custom_plane():
    k = _kernel()
    r = k.mirror(_box(k), plane={"kind": "custom", "point": (15.0, 0.0, 0.0),
                                 "z_dir": (1.0, 0.0, 0.0)})
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(20.0, abs=1e-6)
    assert maxx == pytest.approx(30.0, abs=1e-6)
