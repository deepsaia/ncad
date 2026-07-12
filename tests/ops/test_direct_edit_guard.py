from ncad.ops.direct_edit_guard import DirectEditGuard, GuardVerdict
from ncad.refs.element import Element
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, w=20.0, d=20.0, h=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), h)


def _face_element(kernel, solid) -> Element:
    # The guard receives the resolved face Element (handle + attrs), as the builder passes it.
    d = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"][0]
    return Element(id="#face/t/00000000", kind="face", created_by="t", tag=None,
                   attrs={"geom_type": d["geom_type"], "area": d["area"]}, handle=d["handle"])


def test_defeature_planar_single_body_allowed() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    verdict = DirectEditGuard().check(kernel, solid, _face_element(kernel, solid), "defeature", {})
    assert isinstance(verdict, GuardVerdict) and verdict.allowed


def test_defeature_multibody_refused() -> None:
    kernel = FakeKernel()
    a = _box(kernel)
    b = kernel.transform(_box(kernel), move=(50.0, 0.0, 0.0))
    multibody = kernel.union_bodies([a, b], origin="u")
    verdict = DirectEditGuard().check(kernel, multibody, _face_element(kernel, multibody),
                                      "defeature", {})
    assert not verdict.allowed and "multibody" in verdict.reason.lower()


def test_offset_outward_allowed() -> None:
    kernel = FakeKernel()
    solid = _box(kernel)
    verdict = DirectEditGuard().check(kernel, solid, None, "offset", {"distance": 1.0})
    assert verdict.allowed


def test_offset_inward_past_wall_refused() -> None:
    kernel = FakeKernel()
    solid = _box(kernel, 20.0, 20.0, 20.0)  # min wall thickness 20
    verdict = DirectEditGuard().check(kernel, solid, None, "offset", {"distance": -25.0})
    assert not verdict.allowed and "wall" in verdict.reason.lower()
