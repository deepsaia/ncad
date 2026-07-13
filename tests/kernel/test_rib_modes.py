import pytest

pytestmark = pytest.mark.slow


def _bracket():
    # An L bracket: a tall base wall + a perpendicular wall, leaving a reentrant corner a rib
    # would brace.
    from build123d import Solid

    return Solid.make_box(20, 4, 20) + Solid.make_box(4, 20, 20)


def _rib_wire(z):
    from build123d import Edge, Vector, Wire

    return Wire(Edge.make_line(Vector(4, 4, z), Vector(12, 12, z)))


def test_until_material_rib_grows_to_the_target():
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    base = _bracket()
    # An until-material rib grows (downward) until it meets the bracket, auto-trimmed, so it
    # needs no manual boolean-trim (the proper fix for the gate-2.9 workaround).
    blade = kernel.rib(_rib_wire(20), thickness=2.0, to=base)
    assert blade.volume > 0


def test_fixed_depth_rib_still_works():
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    blade = kernel.rib(_rib_wire(10), thickness=2.0, depth=8.0)
    assert blade.volume > 0
