import math

from tests.kernel.fake_kernel import FakeKernel


def test_fake_primitive_volumes():
    kernel = FakeKernel()
    box = kernel.make_primitive("box", {"w": 10.0, "d": 10.0, "h": 10.0}, "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(box), 1000.0, rel_tol=1e-6)
    sphere = kernel.make_primitive("sphere", {"radius": 10.0}, "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(sphere), 4.0 / 3.0 * math.pi * 1000.0, rel_tol=1e-6)
    cyl = kernel.make_primitive("cylinder", {"radius": 5.0, "h": 20.0}, "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(cyl), math.pi * 25.0 * 20.0, rel_tol=1e-6)
    torus = kernel.make_primitive("torus", {"major_radius": 30.0, "minor_radius": 4.0},
                                  "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(torus), 2.0 * math.pi ** 2 * 30.0 * 16.0, rel_tol=1e-6)
    wedge = kernel.make_primitive("wedge", {"dx": 20.0, "dy": 10.0, "dz": 15.0}, "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(wedge), 3000.0, rel_tol=1e-6)
    cone = kernel.make_primitive("cone", {"bottom_radius": 10.0, "top_radius": 0.0, "h": 20.0},
                                 "XY", (0.0, 0.0))
    assert math.isclose(kernel.volume(cone), math.pi / 3.0 * 20.0 * 100.0, rel_tol=1e-6)
