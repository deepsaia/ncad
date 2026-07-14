from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
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


def _cyl_face(axis_loc, axis_dir, radius, center) -> Element:
    return Element(id="#face/c/00000000", kind="face", created_by="c", tag=None,
                   attrs={"geom_type": "cylinder", "axis_location": axis_loc,
                          "axis_direction": axis_dir, "radius": radius, "center": center,
                          "normal": (1.0, 0.0, 0.0), "area": 50.0}, handle=object())


def test_relate_coaxial_applies() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _cyl_face((0, 0, 0), (0, 0, 1), 4.0, (0, 0, 5))
    moving = _cyl_face((5, 0, 0), (0, 0, 1), 4.0, (5, 0, 5))
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "coaxial",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_relate_coaxial_noncylindrical_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))  # planar, no axis
    moving = _cyl_face((5, 0, 0), (0, 0, 1), 4.0, (5, 0, 5))
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "coaxial",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "rel"


def test_relate_tangent_cylinder_to_cylinder_applies() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _cyl_face((0, 0, 0), (0, 0, 1), 5.0, (0, 0, 5))
    moving = _cyl_face((20, 0, 0), (0, 0, 1), 3.0, (20, 0, 5))  # cylindrical moving face
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "tangent",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_relate_tangent_plane_to_cylinder_applies() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _cyl_face((0, 0, 0), (0, 0, 1), 5.0, (0, 0, 5))
    moving = _face((1.0, 0.0, 0.0), (20.0, 0.0, 0.0))  # planar +X at x=20
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "tangent",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def _two_body_set(kernel) -> BodySet:
    a = _box(kernel)
    b = _box(kernel)
    return BodySet([Body(id="base/body/0", kind="solid", shape=a, created_by="base"),
                    Body(id="base/body/1", kind="solid", shape=b, created_by="second")])


def test_relate_moving_body_moves_only_the_named_body() -> None:
    kernel = FakeKernel()
    bodies = _two_body_set(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    moving = _face((1.0, 0.0, 0.0), (5.0, 0.0, 5.0))
    result = RelationalEditOp().build(
        bodies, {"id": "rel", "relation": "parallel", "moving_body": "base/body/1",
                 "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert isinstance(result.shape, BodySet)
    # Both bodies survive with their born-once ids and provenance; only body/1's shape changed.
    ids = result.shape.ids()
    assert ids == ["base/body/0", "base/body/1"]
    assert result.shape.by_id("base/body/0").shape is bodies.by_id("base/body/0").shape
    assert result.shape.by_id("base/body/1").shape is not bodies.by_id("base/body/1").shape
    assert result.shape.by_id("base/body/1").created_by == "second"


def test_relate_moving_body_on_single_body_shape_is_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    moving = _face((1.0, 0.0, 0.0), (5.0, 0.0, 5.0))
    result = RelationalEditOp().build(
        solid, {"id": "rel", "relation": "parallel", "moving_body": "x/body/0",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "rel"


def test_relate_moving_body_unknown_id_is_refused() -> None:
    kernel = FakeKernel()
    bodies = _two_body_set(kernel)
    ref = _face((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    moving = _face((1.0, 0.0, 0.0), (5.0, 0.0, 5.0))
    result = RelationalEditOp().build(
        bodies, {"id": "rel", "relation": "parallel", "moving_body": "base/body/9",
                 "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and "unknown body id" in errors[0].message
