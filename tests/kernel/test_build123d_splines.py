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


def test_project_spline_edge_is_not_supported():
    from ncad.kernel.build123d_kernel import _build_edge, _project_edge
    basis = _kernel_basis()
    edge = _build_edge({"kind": "bezier", "points": [(0, 0), (1, 2), (3, 2), (4, 0)]}, basis)
    with pytest.raises(NotImplementedError, match="spline"):
        _project_edge(edge, basis)
