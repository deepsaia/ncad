import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k):
    return k.extrude(k.polygon_face([(-10, -10), (10, -10), (10, 10), (-10, 10)], "XY"),
                     distance=20.0)


def _vertical_edges(k, box):
    from ncad.ops.edge_selector import EdgeSelector
    return EdgeSelector().select(k.edges_of(box), "vertical")


def test_symmetric_chamfer_still_builds():
    k = _kernel()
    box = _box(k)
    v0 = k.volume(box)
    result = k.chamfer_edges(box, _vertical_edges(k, box), 3.0)
    assert 0 < k.volume(result) < v0


def test_two_distance_chamfer_builds():
    k = _kernel()
    box = _box(k)
    v0 = k.volume(box)
    result = k.chamfer_edges(box, _vertical_edges(k, box), 3.0, distance2=6.0)
    assert 0 < k.volume(result) < v0


def test_distance_angle_chamfer_builds():
    k = _kernel()
    box = _box(k)
    v0 = k.volume(box)
    result = k.chamfer_edges(box, _vertical_edges(k, box), 3.0, angle=30.0)
    assert 0 < k.volume(result) < v0
