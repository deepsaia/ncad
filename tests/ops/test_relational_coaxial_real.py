import math

import pytest

pytestmark = pytest.mark.slow


def _cylinder(kernel, cx, cy, diameter=10.0, height=20.0, z0=0.0):
    return kernel.extrude(kernel.circle_face((cx, cy), diameter, "XY", z0), height)


def _cyl_element(kernel, solid):
    d = next(d for d in kernel.describe_elements(solid)
             if d["kind"] == "face" and d["geom_type"] == "cylinder")
    from ncad.refs.element import Element

    return Element(id="#face/c/00000000", kind="face", created_by="c", tag=None,
                   attrs={"geom_type": "cylinder", "axis_location": d["axis_location"],
                          "axis_direction": d["axis_direction"], "radius": d["radius"],
                          "center": d["center"], "normal": d["normal"], "area": 1.0},
                   handle=d["handle"])


def _axis_line(kernel, solid):
    d = next(d for d in kernel.describe_elements(solid)
             if d["kind"] == "face" and d["geom_type"] == "cylinder")
    return d["axis_location"], d["axis_direction"]


def test_relate_coaxial_aligns_two_cylinders_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.relational_edit_op import RelationalEditOp

    kernel = Build123dKernel()
    fixed = _cylinder(kernel, 0.0, 0.0)          # axis along Z through origin
    mover = _cylinder(kernel, 40.0, 0.0)         # axis along Z through (40,0)
    ref = _cyl_element(kernel, fixed)
    moving = _cyl_element(kernel, mover)
    result = RelationalEditOp().build(
        mover, {"id": "rel", "relation": "coaxial",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None and not [i for i in result.issues if i.level == "error"]
    # The moved cylinder's axis is now collinear with the reference axis (through origin, +/-Z).
    loc, direction = _axis_line(kernel, result.shape)
    assert abs(direction[2]) > 0.999          # still Z-aligned
    assert math.hypot(loc[0], loc[1]) < 1e-6  # axis passes through (0,0) in XY


def test_relate_tangent_plane_to_cylinder_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.relational_edit_op import RelationalEditOp

    kernel = Build123dKernel()
    cyl = _cylinder(kernel, 0.0, 0.0, diameter=10.0)   # radius 5, axis along Z
    block = kernel.extrude(
        kernel.polygon_face([(30, -5), (40, -5), (40, 5), (30, 5)], "XY"), 20.0)
    ref = _cyl_element(kernel, cyl)
    # The block's -X face (normal pointing toward the cylinder) is the moving planar face.
    moving_d = min((d for d in kernel.describe_elements(block)
                    if d["kind"] == "face" and d["geom_type"] == "plane"
                    and abs(d["normal"][0]) > 0.9),
                   key=lambda d: d["center"][0])
    from ncad.refs.element import Element

    moving = Element(id="#face/m/00000000", kind="face", created_by="m", tag=None,
                     attrs={"geom_type": "plane", "normal": moving_d["normal"],
                            "center": moving_d["center"], "area": moving_d["area"]},
                     handle=moving_d["handle"])
    result = RelationalEditOp().build(
        block, {"id": "rel", "relation": "tangent",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None and not [i for i in result.issues if i.level == "error"]
    # The moved block's nearest planar-X face now sits at radius 5 from the cylinder axis (Z).
    moved = min((d for d in kernel.describe_elements(result.shape)
                 if d["kind"] == "face" and d["geom_type"] == "plane"
                 and abs(d["normal"][0]) > 0.9),
                key=lambda d: abs(d["center"][0]))
    assert math.isclose(abs(moved["center"][0]), 5.0, abs_tol=1e-6)
