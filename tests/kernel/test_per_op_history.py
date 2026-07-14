import pytest

pytestmark = pytest.mark.slow


def test_fillet_history_marks_only_the_rounded_faces_generated():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    rounded = kernel.fillet_edges(box, [box.edges()[0]], 2.0)
    hist = kernel.history([box], rounded)
    # A single-edge fillet GENERATES only the rounded face(s), not every output face (the coarse
    # "all faces generated" history was wrong and defeated persistent naming of carried faces).
    total_faces = len(rounded.faces())
    assert 0 < len(hist.generated_from) < total_faces


def test_chamfer_history_has_lineage():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    beveled = kernel.chamfer_edges(box, [box.edges()[0]], 2.0)
    hist = kernel.history([box], beveled)
    total_faces = len(beveled.faces())
    assert 0 < len(hist.generated_from) < total_faces


def test_revolve_history_generates_walls_from_profile_edges():
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    profile = kernel.polygon_face([(2, 0), (8, 0), (8, 20), (2, 20)], "XZ")
    solid = kernel.revolve(profile, (0, 0, 0), (0, 0, 1), angle=360.0)
    hist = kernel.history([profile], solid)
    # The side walls are generated from the profile's edges (real per-op lineage), so at least
    # one output face has recorded generated-from lineage.
    assert len(hist.generated_from) >= 1
