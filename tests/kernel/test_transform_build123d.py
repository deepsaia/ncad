import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), distance=10)


def test_move_shifts_center():
    k = _kernel()
    r = k.transform(_box(k), move=(20.0, 0.0, 0.0))
    assert k.volume(r) == pytest.approx(1000.0, rel=1e-6)
    (minx, _, _), (maxx, _, _) = k.bounding_box(r)
    assert minx == pytest.approx(20.0, abs=1e-6)


def test_rotate_preserves_volume():
    k = _kernel()
    r = k.transform(_box(k), rotate={"axis": (0.0, 0.0, 1.0), "angle": 45.0,
                                     "about": (0.0, 0.0, 0.0)})
    assert k.volume(r) == pytest.approx(1000.0, rel=1e-6)


def test_uniform_scale_cubes_volume():
    k = _kernel()
    r = k.transform(_box(k), scale=2.0)
    assert k.volume(r) == pytest.approx(8000.0, rel=1e-6)


def test_non_uniform_scale_multiplies_by_product():
    k = _kernel()
    r = k.transform(_box(k), scale=(2.0, 1.0, 0.5))
    assert k.volume(r) == pytest.approx(1000.0, rel=1e-6)


def test_transform_bodyset_moves_each_body_preserving_ids():
    k = _kernel()
    bs = k.union_bodies([_box(k), _box(k)], origin="g")  # g/body/0, g/body/1
    r = k.transform(bs, move=(20.0, 0.0, 0.0))
    assert [b.id for b in k.bodies(r)] == ["g/body/0", "g/body/1"]
    assert k.volume(r) == pytest.approx(2000.0, rel=1e-6)
