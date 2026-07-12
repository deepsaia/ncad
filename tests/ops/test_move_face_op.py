from ncad.ops.move_face_op import MoveFaceOp
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, s=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def _face_element(kernel, solid, geom_type="plane") -> Element:
    d = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"][0]
    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": geom_type, "area": d["area"]}, handle=d["handle"])


def test_move_face_outward_succeeds() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    face = _face_element(kernel, solid)
    result = MoveFaceOp().build(solid, {"id": "mf", "distance": 2.0, "__refs__": {"face": face}},
                                {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_move_face_nonplanar_refused_with_issue() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    face = _face_element(kernel, solid, geom_type="cylinder")
    result = MoveFaceOp().build(solid, {"id": "mf", "distance": 2.0, "__refs__": {"face": face}},
                                {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "mf"
