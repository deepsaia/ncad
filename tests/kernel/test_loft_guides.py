import pytest

pytestmark = pytest.mark.slow


def test_guided_loft_follows_a_rail():
    from build123d import Edge, Plane, Vector, Wire

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    # Two circular sections stacked 20 apart; a guide rail that bows outward in x pulls the
    # loft to follow it (a guided loft, not a straight blend).
    bottom = Wire(Edge.make_circle(3, Plane(origin=Vector(0, 0, 0))))
    top = Wire(Edge.make_circle(3, Plane(origin=Vector(0, 0, 20))))
    guide = Wire(Edge.make_line(Vector(3, 0, 0), Vector(8, 0, 20)))

    solid = kernel.loft([_face(bottom), _face(top)], guides=[guide])
    assert solid.volume > 0


def _face(wire):
    from build123d import Face

    return Face(wire)


def test_closed_loft_is_called_out_as_unsupported():
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.kernel.kernel_op_error import KernelOpError

    kernel = Build123dKernel()
    with pytest.raises(KernelOpError, match="closed"):
        kernel.loft([], closed=True)
