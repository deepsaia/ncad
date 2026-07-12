import pytest

pytestmark = pytest.mark.slow


def _box(kernel, s=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def _element(descriptor):
    from ncad.refs.element import Element

    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": descriptor["geom_type"], "area": descriptor["area"]},
                   handle=descriptor["handle"])


def test_move_planar_box_face_succeeds_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.move_face_op import MoveFaceOp

    kernel = Build123dKernel()
    box = _box(kernel)
    top = max((d for d in kernel.describe_elements(box) if d["kind"] == "face"),
              key=lambda d: d["mid_z"])
    result = MoveFaceOp().build(
        box, {"id": "mf", "distance": 3.0, "__refs__": {"face": _element(top)}}, {}, kernel)
    assert result.shape is not None and not [i for i in result.issues if i.level == "error"]


def test_move_face_next_to_fillet_refused_real() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.move_face_op import MoveFaceOp

    kernel = Build123dKernel()
    box = _box(kernel)
    filleted = kernel.fillet_edges(box, [kernel.edges_of(box)[0]["edge"]], 4.0)
    # A planar face adjacent to the fillet: its neighbour set includes the cylinder, so refused.
    faces = [d for d in kernel.describe_elements(filleted) if d["kind"] == "face"]
    planar = [d for d in faces if d["geom_type"] == "plane"]
    picked = None
    for d in planar:
        neighbours = kernel.face_neighbours(filleted, d["handle"])
        for other in faces:
            if other["geom_type"] != "cylinder":
                continue
            owr = other["handle"].wrapped
            if any(owr.IsSame(n) for n in neighbours):
                picked = d
                break
        if picked is not None:
            break
    assert picked is not None, "expected a planar face adjacent to the fillet"
    result = MoveFaceOp().build(
        filleted, {"id": "mf", "distance": 2.0, "__refs__": {"face": _element(picked)}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "mf"
    assert "planar" in errors[0].message.lower()
