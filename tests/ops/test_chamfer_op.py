from ncad.ops.chamfer_op import ChamferOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(-5, -5), (5, -5), (5, 5), (-5, 5)], "XY"),
                     distance=10.0)


def test_symmetric_chamfer_routes_to_kernel():
    k = FakeKernel()
    box = _box(k)
    result = ChamferOp().build(box, {"id": "ch", "edges": "all", "distance": 2}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) < k.volume(box)


def test_two_distance_chamfer_routes_to_kernel():
    k = FakeKernel()
    box = _box(k)
    result = ChamferOp().build(
        box, {"id": "ch", "edges": "all", "distance": 2, "distance2": 6}, {}, k)
    assert result.shape is not None


def test_distance_angle_chamfer_routes_to_kernel():
    k = FakeKernel()
    box = _box(k)
    result = ChamferOp().build(
        box, {"id": "ch", "edges": "all", "distance": 2, "angle": 30}, {}, k)
    assert result.shape is not None


def test_both_modes_reports_issue():
    k = FakeKernel()
    box = _box(k)
    result = ChamferOp().build(
        box, {"id": "ch", "edges": "all", "distance": 2, "distance2": 6, "angle": 30}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
