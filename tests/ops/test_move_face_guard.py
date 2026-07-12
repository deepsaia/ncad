from ncad.ops.direct_edit_guard import DirectEditGuard
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, s=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def _face_element(kernel, solid, geom_type="plane") -> Element:
    d = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"][0]
    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": geom_type, "area": d["area"]}, handle=d["handle"])


def test_move_face_planar_simple_allowed() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    verdict = DirectEditGuard().check(kernel, solid, _face_element(kernel, solid),
                                      "move_face", {"distance": 2.0})
    assert verdict.allowed


def test_move_face_nonplanar_target_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    face = _face_element(kernel, solid, geom_type="cylinder")
    verdict = DirectEditGuard().check(kernel, solid, face, "move_face", {"distance": 2.0})
    assert not verdict.allowed and "planar" in verdict.reason.lower()


def test_move_face_inward_past_wall_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel, 20.0)  # min wall 20
    verdict = DirectEditGuard().check(kernel, solid, _face_element(kernel, solid),
                                      "move_face", {"distance": -25.0})
    assert not verdict.allowed and "wall" in verdict.reason.lower()
