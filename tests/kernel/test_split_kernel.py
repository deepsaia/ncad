import pytest

from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_split_both_returns_two_shapes_summing_to_volume():
    k = FakeKernel()
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 5.0}, keep="both")
    assert len(parts) == 2
    assert k.volume(parts[0]) + k.volume(parts[1]) == pytest.approx(1000.0)


def test_split_both_partitions_by_plane_fraction():
    k = FakeKernel()
    # box x in [0,10]; split at x=2 -> top side x in [2,10] (fraction 0.8), bottom x in [0,2] (0.2)
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 2.0}, keep="both")
    # parts[0] = TOP (positive side of +X normal) = x in [2,10] -> 800; parts[1] = BOTTOM -> 200
    assert k.volume(parts[0]) == pytest.approx(800.0)
    assert k.volume(parts[1]) == pytest.approx(200.0)


def test_split_top_returns_one_shape():
    k = FakeKernel()
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 2.0}, keep="top")
    assert len(parts) == 1
    assert k.volume(parts[0]) == pytest.approx(800.0)


def test_split_bottom_returns_one_shape():
    k = FakeKernel()
    parts = k.split(_box(k), plane={"kind": "base", "plane": "YZ", "offset": 2.0}, keep="bottom")
    assert len(parts) == 1
    assert k.volume(parts[0]) == pytest.approx(200.0)
