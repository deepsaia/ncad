import pytest

pytestmark = pytest.mark.slow


def _box(kernel, w=40.0, d=40.0, h=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), h)


def _element_for_descriptor(descriptor):
    from ncad.refs.element import Element

    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": descriptor["geom_type"], "area": descriptor["area"]},
                   handle=descriptor["handle"])


def test_outward_offset_accepted_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.offset_face_op import OffsetFaceOp

    kernel = Build123dKernel()
    result = OffsetFaceOp().build(_box(kernel), {"id": "of", "distance": 1.0, "__refs__": {}},
                                  {}, kernel)
    assert result.shape is not None and not [i for i in result.issues if i.level == "error"]


def test_inward_offset_past_wall_refused_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.offset_face_op import OffsetFaceOp

    kernel = Build123dKernel()
    box = _box(kernel, 40.0, 40.0, 20.0)  # min wall 20
    result = OffsetFaceOp().build(box, {"id": "of", "distance": -25.0, "__refs__": {}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "of"


def test_defeature_tangent_adjacent_refused_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.defeature_op import DefeatureOp

    kernel = Build123dKernel()
    box = _box(kernel)
    # Fillet an edge to create a tangent-adjacent face, then defeature a planar face that is
    # itself tangent-adjacent to the fillet (the guard must refuse it).
    filleted = kernel.fillet_edges(box, [kernel.edges_of(box)[0]["edge"]], 4.0)
    planar_tangent = [d for d in kernel.describe_elements(filleted)
                      if d["kind"] == "face" and d["geom_type"] == "plane"
                      and kernel.is_tangent_adjacent(filleted, d["handle"])]
    assert planar_tangent, "expected a planar face tangent-adjacent to the fillet"
    face = _element_for_descriptor(planar_tangent[0])
    result = DefeatureOp().build(filleted, {"id": "df", "__refs__": {"face": face}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "df"
    assert "tangent" in errors[0].message.lower()
