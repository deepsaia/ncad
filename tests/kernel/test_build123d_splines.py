import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _kernel_basis():
    from ncad.kernel.build123d_kernel import _PLANES
    return _PLANES["XY"]


def test_bezier_wire_builds():
    # wire_face returns a build123d Face; measure its native .area.
    k = _kernel()
    edges = [{"kind": "bezier", "points": [(0, 0), (1, 2), (3, 2), (4, 0)]},
             {"kind": "line", "points": [(4, 0), (0, 0)]}]
    face = k.wire_face(edges, "XY")
    assert face.area > 0


def test_interpolated_spline_wire_builds():
    k = _kernel()
    edges = [{"kind": "spline", "points": [(0, 0), (2, 3), (4, 0)]},
             {"kind": "line", "points": [(4, 0), (0, 0)]}]
    face = k.wire_face(edges, "XY")
    assert face.area > 0


def test_open_bezier_path_wire_has_length():
    # wire returns a build123d Wire; measure its native .length.
    k = _kernel()
    wire = k.wire([{"kind": "bezier", "points": [(0, 0), (1, 2), (3, 2), (4, 0)]}], "XZ")
    assert wire.length > 0


def test_project_spline_edge_samples_an_interpolated_curve():
    from ncad.kernel.build123d_kernel import _build_edge, _project_edge
    basis = _kernel_basis()
    edge = _build_edge({"kind": "bezier", "points": [(0, 0), (1, 2), (3, 2), (4, 0)]}, basis)
    # A curved edge projects to a sampled interpolated spline descriptor (no longer refused).
    descriptor = _project_edge(edge, basis)
    assert descriptor["kind"] == "spline"
    assert len(descriptor["points"]) >= 3
    # The sampled endpoints match the curve's endpoints (start (0,0), end (4,0) on the plane).
    first, last = descriptor["points"][0], descriptor["points"][-1]
    assert abs(first[0]) < 1e-6 and abs(first[1]) < 1e-6
    assert abs(last[0] - 4.0) < 1e-6 and abs(last[1]) < 1e-6
