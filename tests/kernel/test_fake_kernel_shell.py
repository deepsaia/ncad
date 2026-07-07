from tests.kernel.fake_kernel import FakeKernel


def _box(k, w=20.0, h=20.0, d=20.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, h), (0, h)], "XY"), distance=d)


def test_shell_volume_is_wall_only():
    # Outer 20x20x20 = 8000; inner shrunk 2*t=4 per axis >> 16*16*16 = 4096; wall = 3904.
    k = FakeKernel()
    box = _box(k)
    result = k.shell(box, 2.0)
    assert k.volume(result) == 8000 - 16 * 16 * 16


def test_shell_volume_monotonic_in_thickness():
    k = FakeKernel()
    box = _box(k)
    thin = k.volume(k.shell(box, 1.0))
    thick = k.volume(k.shell(box, 3.0))
    assert thick > thin > 0


def test_shell_thick_wall_clamps_inner_to_zero():
    # thickness so large the inner box vanishes: wall == whole outer volume.
    k = FakeKernel()
    box = _box(k, 10, 10, 10)
    result = k.shell(box, 8.0)  # 2*8 > 10 on every axis >> inner 0
    assert k.volume(result) == 1000
