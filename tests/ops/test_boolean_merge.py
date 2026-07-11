from ncad.kernel.body_set import BodySet
from ncad.ops.boolean_op import BooleanOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k, x0, w):
    return k.extrude(k.polygon_face([(x0, 0), (x0 + w, 0), (x0 + w, 5), (x0, 5)], "XY"),
                     distance=5)


def test_union_merge_true_fuses_to_one_shape():
    k = FakeKernel()
    a, b = _box(k, 0, 4), _box(k, 10, 4)  # disjoint
    result = BooleanOp().build(None, {"id": "u", "operation": "union", "target": "a",
                                      "tool": "b", "__refs__": {"target": a, "tool": b}}, {}, k)
    assert result.shape is not None
    assert not isinstance(result.shape, BodySet)  # fused: a plain shape


def test_union_merge_false_keeps_two_bodies_with_ids():
    k = FakeKernel()
    a, b = _box(k, 0, 4), _box(k, 10, 4)
    result = BooleanOp().build(None, {"id": "u", "operation": "union", "merge": False,
                                      "target": "a", "tool": "b",
                                      "__refs__": {"target": a, "tool": b}}, {}, k)
    assert isinstance(result.shape, BodySet)
    assert len(result.shape) == 2
    assert result.shape.ids() == ["u/body/0", "u/body/1"]
    # ids are born under the union origin, but each body keeps its SOURCE feature as created_by
    # (so per-body provenance/material survives the keep-separate union).
    assert [bd.created_by for bd in result.shape.bodies] == ["a", "b"]
