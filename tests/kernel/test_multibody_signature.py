from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
from tests.kernel.fake_kernel import FakeKernel


def _box(k, x0, w):
    return k.extrude(k.polygon_face([(x0, 0), (x0 + w, 0), (x0 + w, 3), (x0, 3)], "XY"),
                     distance=3)


def test_multibody_signature_has_per_body_list():
    k = FakeKernel()
    bs = BodySet([Body(id="u/body/0", kind="solid", shape=_box(k, 0, 2), created_by="u"),
                  Body(id="u/body/1", kind="solid", shape=_box(k, 9, 4), created_by="u")])
    sig = k.signature(bs)
    assert "bodies" in sig and len(sig["bodies"]) == 2


def test_multibody_signature_order_independent():
    k = FakeKernel()
    x = Body(id="u/body/0", kind="solid", shape=_box(k, 0, 2), created_by="u")
    y = Body(id="u/body/1", kind="solid", shape=_box(k, 9, 4), created_by="u")
    assert k.signature(BodySet([x, y])) == k.signature(BodySet([y, x]))


def test_single_shape_signature_unchanged_shape():
    k = FakeKernel()
    sig = k.signature(_box(k, 0, 2))
    assert "bodies" not in sig  # single-body signature is the flat dict, as before
