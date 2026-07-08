import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k, w, d, h):
    return k.extrude(k.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), distance=h)


def _bodyset(k):
    from ncad.kernel.body import Body
    from ncad.kernel.body_set import BodySet
    a = _box(k, 2, 2, 2)
    b = _box(k, 3, 3, 3)
    return BodySet([Body(id="p/body/0", kind="solid", shape=a, created_by="p"),
                    Body(id="p/body/1", kind="solid", shape=b, created_by="p")])


def test_build123d_bodies_of_single_shape_is_one_body():
    k = _kernel()
    bodies = k.bodies(_box(k, 5, 5, 5))
    assert len(bodies) == 1 and bodies[0].kind == "solid"


def test_build123d_bodyset_volume_is_sum():
    k = _kernel()
    assert k.volume(_bodyset(k)) == pytest.approx(8 + 27, rel=1e-6)
