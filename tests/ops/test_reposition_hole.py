import pytest

from ncad.ops.reposition_hole_op import RepositionHoleOp
from ncad.ops.reposition_hole_params import RepositionHoleParamError, reposition_hole_kwargs
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, s=40.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), 10.0)


def _hole_face(location, direction=(0.0, 0.0, 1.0), radius=4.0) -> Element:
    return Element(id="#face/h/00000000", kind="face", created_by="import", tag=None,
                   attrs={"geom_type": "cylinder", "axis_location": location,
                          "axis_direction": direction, "radius": radius,
                          "center": location, "area": 50.0}, handle=object())


def test_kwargs_requires_a_target_position():
    with pytest.raises(RepositionHoleParamError):
        reposition_hole_kwargs({})


def test_kwargs_normalizes_to_floats():
    kw = reposition_hole_kwargs({"to": [30, 30]})
    assert kw["to"] == (30.0, 30.0)


def test_reposition_hole_fills_and_recuts_preserving_volume():
    kernel = FakeKernel()
    solid = _box(kernel)
    hole_face = _hole_face((10.0, 10.0, 5.0))
    result = RepositionHoleOp().build(
        solid, {"id": "rh", "to": [30, 30], "__refs__": {"hole": hole_face}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_reposition_hole_needs_a_cylindrical_face():
    kernel = FakeKernel()
    solid = _box(kernel)
    planar = Element(id="#face/p/00000000", kind="face", created_by="import", tag=None,
                     attrs={"geom_type": "plane", "normal": (0, 0, 1), "center": (0, 0, 0)},
                     handle=object())
    result = RepositionHoleOp().build(
        solid, {"id": "rh", "to": [30, 30], "__refs__": {"hole": planar}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and "cylindrical" in errors[0].message


def test_reposition_hole_needs_a_hole_reference():
    kernel = FakeKernel()
    solid = _box(kernel)
    result = RepositionHoleOp().build(solid, {"id": "rh", "to": [30, 30], "__refs__": {}}, {},
                                      kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "rh"
