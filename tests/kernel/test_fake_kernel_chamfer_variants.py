from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(-5, -5), (5, -5), (5, 5), (-5, 5)], "XY"),
                     distance=10.0)


def test_symmetric_chamfer_delta_unchanged():
    k = FakeKernel()
    box = _box(k)
    v0 = k.volume(box)
    # 3 edges, distance 2 >> subtract 2 * 3.
    result = k.chamfer_edges(box, [object(), object(), object()], 2.0)
    assert k.volume(result) == v0 - 2.0 * 3


def test_two_distance_uses_mean_setback():
    k = FakeKernel()
    box = _box(k)
    v0 = k.volume(box)
    # mean of (2, 6) = 4, over 2 edges >> subtract 8.
    result = k.chamfer_edges(box, [object(), object()], 2.0, distance2=6.0)
    assert k.volume(result) == v0 - 4.0 * 2


def test_distance_angle_uses_first_setback():
    k = FakeKernel()
    box = _box(k)
    v0 = k.volume(box)
    # first setback 3 drives the cut; angle only reshapes. 2 edges >> subtract 6.
    result = k.chamfer_edges(box, [object(), object()], 3.0, angle=30.0)
    assert k.volume(result) == v0 - 3.0 * 2
