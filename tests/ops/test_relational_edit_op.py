from ncad.ops.relational_edit_op import RelationalEditOp
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, s=10.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def _face(normal, center, geom_type="plane") -> Element:
    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": geom_type, "normal": normal, "center": center,
                          "area": 100.0}, handle=object())


def test_relate_parallel_applies_and_returns_solid() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    moving = _face((1.0, 0.0, 0.0), (5.0, 0.0, 5.0))
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "parallel",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_relate_nonplanar_reference_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _face((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), geom_type="cylinder")
    moving = _face((0.0, 0.0, 1.0), (0.0, 0.0, 5.0))
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "parallel",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "rel"


def test_relate_already_satisfied_returns_input() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    moving = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))  # already coplanar+parallel
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "parallel",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is solid  # unchanged
