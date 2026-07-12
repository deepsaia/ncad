from ncad.ops.defeature_op import DefeatureOp
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel):
    return kernel.extrude(kernel.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"), 20.0)


def _face_element(kernel, solid) -> Element:
    d = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"][0]
    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": d["geom_type"], "area": d["area"]}, handle=d["handle"])


def test_defeature_allowed_face_succeeds() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    face = _face_element(kernel, solid)
    result = DefeatureOp().build(solid, {"id": "df", "__refs__": {"face": face}}, {}, kernel)
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_defeature_multibody_refused_with_issue() -> None:
    kernel = FakeKernel()
    a = _box(kernel)
    b = kernel.transform(_box(kernel), move=(50.0, 0.0, 0.0))
    multibody = kernel.union_bodies([a, b], origin="u")
    face = _face_element(kernel, multibody)
    result = DefeatureOp().build(multibody, {"id": "df", "__refs__": {"face": face}}, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "df"
