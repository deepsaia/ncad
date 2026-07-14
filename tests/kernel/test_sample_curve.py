import pytest

pytestmark = pytest.mark.slow


def test_sample_line_uniformly():
    from build123d import Edge, Vector, Wire

    from ncad.kernel.build123d_kernel import Build123dKernel

    wire = Wire([Edge.make_line(Vector(0, 0, 0), Vector(30, 0, 0))])
    samples = Build123dKernel().sample_curve(wire, 4)
    assert len(samples) == 4
    (p0, _t0) = samples[0]
    (p3, _t3) = samples[-1]
    assert abs(p0[0] - 0.0) < 1e-6
    assert abs(p3[0] - 30.0) < 1e-6
    # Uniform spacing along the line: the middle samples are at 10 and 20.
    assert abs(samples[1][0][0] - 10.0) < 1e-6
    assert abs(samples[2][0][0] - 20.0) < 1e-6


def test_sample_returns_point_and_tangent_tuples():
    from build123d import Edge, Vector, Wire

    from ncad.kernel.build123d_kernel import Build123dKernel

    wire = Wire([Edge.make_line(Vector(0, 0, 0), Vector(0, 0, 10))])
    samples = Build123dKernel().sample_curve(wire, 2)
    point, tangent = samples[0]
    assert len(point) == 3 and len(tangent) == 3
