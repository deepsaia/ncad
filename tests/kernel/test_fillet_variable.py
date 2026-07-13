import pytest

pytestmark = pytest.mark.slow


def test_variable_fillet_builds_and_ramps():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    # Edges must come from the SAME solid instance passed to the kernel (a fresh make_box
    # produces distinct TopoDS edges the maker will not recognize).
    box_v = Solid.make_box(20, 20, 20)
    variable = kernel.fillet_variable(box_v, [box_v.edges()[0]], 2.0, 6.0)

    box_c = Solid.make_box(20, 20, 20)
    constant2 = kernel.fillet_edges(box_c, [box_c.edges()[0]], 2.0)

    # The ramp removes material (less than the plain box) and, being 2 -> 6, removes strictly
    # more than a constant radius 2.
    assert variable.volume < Solid.make_box(20, 20, 20).volume
    assert variable.volume < constant2.volume
