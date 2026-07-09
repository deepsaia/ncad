import pytest

from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_move_preserves_volume_and_shifts_bounds():
    k = FakeKernel()
    r = k.transform(_box(k), move=(20.0, 0.0, 0.0))
    assert k.volume(r) == pytest.approx(1000.0)
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(20.0) and maxx == pytest.approx(30.0)


def test_rotate_preserves_volume():
    k = FakeKernel()
    r = k.transform(_box(k), rotate={"axis": (0.0, 0.0, 1.0), "angle": 45.0,
                                     "about": (0.0, 0.0, 0.0)})
    assert k.volume(r) == pytest.approx(1000.0)


def test_uniform_scale_cubes_volume():
    k = FakeKernel()
    r = k.transform(_box(k), scale=2.0)
    assert k.volume(r) == pytest.approx(8000.0)


def test_non_uniform_scale_multiplies_by_product():
    k = FakeKernel()
    r = k.transform(_box(k), scale=(2.0, 1.0, 0.5))
    assert k.volume(r) == pytest.approx(1000.0)  # 1000 * (2*1*0.5)
