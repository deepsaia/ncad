import pytest

pytestmark = pytest.mark.slow


def _block(kernel, s=10.0, z0=0.0):
    face = kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY", z0)
    return kernel.extrude(face, s)


def _top(kernel, solid):
    return max((d for d in kernel.describe_elements(solid) if d["kind"] == "face"),
              key=lambda d: d["mid_z"])


def _element(descriptor):
    from ncad.refs.element import Element

    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": descriptor["geom_type"], "normal": descriptor["normal"],
                          "center": descriptor["center"], "area": descriptor["area"]},
                   handle=descriptor["handle"])


def test_make_coplanar_moves_face_onto_reference_plane_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.relational_edit_op import RelationalEditOp

    kernel = Build123dKernel()
    fixed = _block(kernel, 10.0, 0.0)          # top face at z=10
    mover = _block(kernel, 6.0, 50.0)          # top face far away
    ref = _element(_top(kernel, fixed))
    moving = _element(_top(kernel, mover))
    result = RelationalEditOp().build(
        mover, {"id": "rel", "relation": "coplanar",
                "__refs__": {"reference": ref, "moving": moving}}, {}, kernel)
    assert result.shape is not None and not [i for i in result.issues if i.level == "error"]
    # The mover's top face now sits on the reference plane.
    moved_top = _top(kernel, result.shape)
    assert abs(moved_top["mid_z"] - ref.attrs["center"][2]) < 1e-6


def test_direct_edit_after_history_stack_rebuilds() -> None:
    # Mixed mode: a parametric history stack (sketch>>extrude>>fillet) then a direct offset.
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry

    document = {"parts": {"p": {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
        {"id": "base", "op": "extrude", "profile": "sk", "distance": 20},
        {"id": "rnd", "op": "fillet", "edges": "select edges where created_by = 'base'",
         "radius": 3},
        {"id": "grow", "op": "offset", "distance": 1},
    ]}}}
    builder = Builder(Build123dKernel(), OpRegistry.with_defaults())
    result, _, _ = builder.build_part_mapped(document["parts"]["p"])
    errors = [i for i in result.issues if i.level == "error"]
    assert result.shape is not None and not errors, errors
