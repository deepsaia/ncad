from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet
from tests.kernel.fake_kernel import FakeKernel


def _box(k, w, d, h):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def test_fake_bodies_of_single_shape_is_one_body():
    k = FakeKernel()
    bodies = k.bodies(_box(k, 10, 10, 10))
    assert len(bodies) == 1 and bodies[0].kind == "solid"


def test_fake_bodyset_volume_is_sum():
    k = FakeKernel()
    a = Body(id="p/body/0", kind="solid", shape=_box(k, 2, 2, 2), created_by="p")
    b = Body(id="p/body/1", kind="solid", shape=_box(k, 3, 3, 3), created_by="p")
    bs = BodySet([a, b])
    assert k.volume(bs) == 8 + 27
