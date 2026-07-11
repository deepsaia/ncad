import pytest

pytestmark = pytest.mark.slow


def test_extrude_history_reports_output_lineage() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.kernel.element_history import ElementHistory

    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)
    hist = kernel.history([face], solid)
    assert isinstance(hist, ElementHistory)
    # An extrude generates side + cap faces; at least one output face has recorded lineage.
    assert len(hist.generated_from) + len(hist.modified_from) >= 1
    assert hist.deleted == []
