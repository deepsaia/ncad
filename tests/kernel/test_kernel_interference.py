import pytest

pytestmark = pytest.mark.slow


def _box(sz):
    from build123d import Box
    return Box(sz, sz, sz)


def test_distance_apart_touching_overlapping() -> None:
    from build123d import Pos

    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    a = _box(10)
    assert k.distance(a, Pos(20, 0, 0) * _box(10)) == pytest.approx(10.0, abs=1e-6)  # gap
    assert k.distance(a, Pos(10, 0, 0) * _box(10)) == pytest.approx(0.0, abs=1e-6)   # flush touch
    assert k.distance(a, Pos(5, 0, 0) * _box(10)) == pytest.approx(0.0, abs=1e-6)    # overlap


def test_common_volume_separates_touch_from_overlap() -> None:
    from build123d import Pos

    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    a = _box(10)
    assert k.common_volume(a, Pos(5, 0, 0) * _box(10)) == pytest.approx(500.0, rel=1e-3)  # 5*10*10
    assert k.common_volume(a, Pos(10, 0, 0) * _box(10)) == pytest.approx(0.0, abs=1e-3)    # touch
    assert k.common_volume(a, Pos(20, 0, 0) * _box(10)) == pytest.approx(0.0, abs=1e-3)    # apart
