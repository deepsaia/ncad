import pytest

from ncad.kernel.body_set import BodySet
from ncad.ops.boolean_op import BooleanOp
from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _solid(kernel, w, h, t):
    face = SketchOp().build(None, {"id": "s", "op": "sketch", "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": w, "h": h}]}, {}, kernel).shape
    return kernel.extrude(face, t)


def _feature(operation, refs, **authored):
    # A real feature dict carries authored keys (target/tool/tools/scope) AND builder-resolved
    # __refs__; the params validator reads the authored keys, the op reads __refs__.
    feature = {"id": "bool", "op": "boolean", "operation": operation, "__refs__": refs}
    feature.update(authored)
    return feature


def test_cut() -> None:
    kernel = FakeKernel()
    a, b = _solid(kernel, 80, 60, 8), _solid(kernel, 20, 20, 8)

    result = BooleanOp().build(None, _feature(
        "cut", {"target": a, "tool": b}, target="a", tool="b"), {}, kernel)

    assert result.issues == []
    assert kernel.volume(result.shape) == pytest.approx(80 * 60 * 8 - 20 * 20 * 8)


def test_union() -> None:
    kernel = FakeKernel()
    a, b = _solid(kernel, 10, 10, 5), _solid(kernel, 10, 10, 5)

    result = BooleanOp().build(None, _feature(
        "union", {"target": a, "tool": b}, target="a", tool="b"), {}, kernel)

    assert kernel.volume(result.shape) == pytest.approx(1000.0)


def test_missing_operand_reports_issue() -> None:
    kernel = FakeKernel()
    a = _solid(kernel, 10, 10, 5)

    # Authored a tool ref but it resolved to None (broken reference).
    result = BooleanOp().build(None, _feature(
        "cut", {"target": a}, target="a", tool="missing"), {}, kernel)

    assert result.shape is None
    assert result.issues[0].node_id == "bool"


def _box(k, w=10.0, d=10.0, h=10.0):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_multi_tool_cut_subtracts_all_tools():
    k = FakeKernel()
    base = _box(k, 10, 10, 10)       # 1000
    t1 = _box(k, 2, 2, 2)            # 8
    t2 = _box(k, 3, 3, 3)            # 27
    result = BooleanOp().build(None, _feature(
        "cut", {"target": base, "tools": [t1, t2]}, target="base", tools=["t1", "t2"]), {}, k)
    assert k.volume(result.shape) == pytest.approx(1000.0 - 8.0 - 27.0)


def test_multi_tool_union_sums():
    k = FakeKernel()
    a = _box(k, 10, 10, 10)
    b = _box(k, 2, 2, 2)
    c = _box(k, 3, 3, 3)
    result = BooleanOp().build(None, _feature(
        "union", {"target": a, "tools": [b, c]}, target="a", tools=["b", "c"]), {}, k)
    assert k.volume(result.shape) == pytest.approx(1000.0 + 8.0 + 27.0)


def _three_body_set(k):
    boxes = [_box(k, 10, 10, 10), _box(k, 10, 10, 10), _box(k, 10, 10, 10)]
    return k.union_bodies(boxes, origin="pat")  # pat/body/0,1,2


def test_scope_union_merges_named_and_passes_through_ids():
    k = FakeKernel()
    running = _three_body_set(k)   # 3 bodies, 1000 each
    result = BooleanOp().build(
        running, {"id": "m", "op": "boolean", "operation": "union",
                  "scope": ["pat/body/0", "pat/body/2"]}, {}, k)
    assert isinstance(result.shape, BodySet)
    # combined body (0+2 fused) gets the new born id m/body/0; pat/body/1 passes through.
    assert set(result.shape.ids()) == {"m/body/0", "pat/body/1"}
    assert k.volume(result.shape) == pytest.approx(3000.0)  # 2000 fused + 1000 passthrough


def test_scope_id_not_found_reports_issue():
    k = FakeKernel()
    running = _three_body_set(k)
    result = BooleanOp().build(
        running, {"id": "m", "op": "boolean", "operation": "union",
                  "scope": ["pat/body/9"]}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_scope_on_single_body_with_multiple_ids_reports_issue():
    k = FakeKernel()
    result = BooleanOp().build(
        _box(k), {"id": "m", "op": "boolean", "operation": "union", "scope": ["a", "b"]},
        {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
