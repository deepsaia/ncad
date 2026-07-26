"""ViewProjector: run a view's HLR projection over a built model (kernel-bound, slow)."""

import pytest

from ncad.drafting.view_projector import ViewProjector
from ncad.kernel.build123d_kernel import Build123dKernel


def _box(kernel: Build123dKernel):
    face = kernel.polygon_face([(0, 0), (30, 0), (30, 20), (0, 20)], "XY")
    return kernel.extrude(face, 10.0)


@pytest.mark.slow
def test_base_view_projects_visible_edges():
    kernel = Build123dKernel()
    projector = ViewProjector(kernel)
    result = projector.project(_box(kernel), {"id": "front", "type": "base", "projection": "XZ"})
    assert result["visible"], "a base view yields visible edges"
    for edge in result["visible"]:
        assert len(edge[0]) == 2


@pytest.mark.slow
def test_iso_view_has_hidden_edges():
    kernel = Build123dKernel()
    projector = ViewProjector(kernel)
    result = projector.project(_box(kernel), {"id": "iso", "type": "iso"})
    assert result["visible"]
    assert result["hidden"], "an isometric view of a solid hides back edges"


@pytest.mark.slow
def test_projected_top_differs_from_front():
    kernel = Build123dKernel()
    projector = ViewProjector(kernel)
    box = _box(kernel)
    front = projector.project(box, {"id": "front", "type": "base", "projection": "XZ"})
    top = projector.project(
        box, {"id": "top", "type": "projected", "from": "front", "direction": "up"},
        parent={"id": "front", "type": "base", "projection": "XZ"})
    # Front looks along -Y; the top projected view looks along -Z, so the visible outline bounds
    # differ (front sees the 30x10 face, top sees the 30x20 face).
    def spans(r):
        xs = [p[0] for e in r["visible"] for p in e]
        ys = [p[1] for e in r["visible"] for p in e]
        return (round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1))
    assert spans(front) != spans(top)
