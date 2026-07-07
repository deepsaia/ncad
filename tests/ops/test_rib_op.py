from ncad.ops.rib_op import RibOp
from tests.kernel.fake_kernel import FakeKernel


def _wire(k):
    return k.wire([{"kind": "line", "points": [(-10.0, 0.0), (10.0, 0.0)]}], "XZ")


def _plate(k):
    return k.extrude(k.polygon_face([(-15, -15), (15, -15), (15, 15), (-15, 15)], "XY"),
                     distance=4.0)


def test_rib_fuses_blade_into_target():
    k = FakeKernel()
    result = RibOp().build(
        None, {"id": "rb", "thickness": 3, "depth": 20,
               "__refs__": {"profile": _wire(k), "target": _plate(k)}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) > 0


def test_rib_uses_shape_in_when_no_target_ref():
    k = FakeKernel()
    result = RibOp().build(
        _plate(k), {"id": "rb", "thickness": 3, "depth": 20,
                    "__refs__": {"profile": _wire(k)}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) > 0


def test_rib_missing_target_reports_issue():
    k = FakeKernel()
    result = RibOp().build(
        None, {"id": "rb", "thickness": 3, "depth": 20,
               "__refs__": {"profile": _wire(k)}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_rib_missing_profile_reports_issue():
    k = FakeKernel()
    result = RibOp().build(
        None, {"id": "rb", "thickness": 3, "depth": 20,
               "__refs__": {"target": _plate(k)}}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
