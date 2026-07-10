import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_split_both_two_valid_solids_summing_to_volume():
    k = _kernel()
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 5.0}, keep="both")
    assert len(parts) == 2
    assert k.volume(parts[0]) + k.volume(parts[1]) == pytest.approx(1000.0, rel=1e-6)
    assert parts[0].is_valid and parts[1].is_valid


def test_split_top_one_side():
    k = _kernel()
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 2.0}, keep="top")
    assert len(parts) == 1
    # TOP is the +X side: x in [2,10] -> volume 800
    assert k.volume(parts[0]) == pytest.approx(800.0, rel=1e-6)
