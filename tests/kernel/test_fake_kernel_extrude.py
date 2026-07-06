from tests.kernel.fake_kernel import FakeKernel


def _square(kernel):
    return kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")


def test_blind_volume():
    k = FakeKernel()
    solid = k.extrude(_square(k), 4)
    assert k.volume(solid) == 10 * 10 * 4


def test_symmetric_same_total_volume():
    k = FakeKernel()
    solid = k.extrude(_square(k), 4, symmetric=True)
    # symmetric extrudes the SAME total distance, centered: volume unchanged from blind
    assert k.volume(solid) == 10 * 10 * 4


def test_two_side_sums_distances():
    k = FakeKernel()
    solid = k.extrude(_square(k), 4, second_distance=3)
    assert k.volume(solid) == 10 * 10 * 7


def test_thin_wall_reduces_volume():
    k = FakeKernel()
    solid = k.extrude(_square(k), 10, thin=2)
    # a 2-wide wall around a 10x10 profile: outer 100 - inner 6x6=36 => 64, * height 10
    assert k.volume(solid) == 64 * 10


def test_until_target_uses_target_bbox_height():
    k = FakeKernel()
    target = k.extrude(_square(k), 12)  # a 12-tall block to extrude "up to"
    solid = k.extrude(_square(k), until="last", target=target)
    assert k.volume(solid) == 10 * 10 * 12
