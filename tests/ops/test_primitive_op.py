from ncad.ops.primitive_op import PrimitiveOp
from tests.kernel.fake_kernel import FakeKernel


def test_primitive_op_builds_a_solid_ignoring_input():
    kernel = FakeKernel()
    result = PrimitiveOp().build(
        None, {"id": "b", "kind": "box", "w": 10, "d": 10, "h": 10}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    assert abs(kernel.volume(result.shape) - 1000.0) < 1e-6


def test_primitive_op_bad_kind_is_id_attributed_issue():
    kernel = FakeKernel()
    result = PrimitiveOp().build(None, {"id": "b", "kind": "prism"}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "b"
