"""Kernel HLR: hidden-line-removal projection returns visible + hidden 2D edges."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel


def _box(kernel: Build123dKernel):
    """A 30x20x10 solid box via the kernel's extrude idiom (no direct box maker)."""
    face = kernel.polygon_face([(0, 0), (30, 0), (30, 20), (0, 20)], "XY")
    return kernel.extrude(face, 10.0)


@pytest.mark.slow
def test_hlr_view_of_a_box_returns_visible_edges():
    kernel = Build123dKernel()
    result = kernel.hlr_view(_box(kernel), direction=(0, 0, -1))  # plan view (look down -Z)
    assert set(result) == {"visible", "hidden"}
    assert result["visible"], "a solid box must yield visible outline edges"
    for edge in result["visible"]:
        assert len(edge) >= 2
        assert len(edge[0]) == 2  # each point is (x, y)


@pytest.mark.slow
def test_hlr_view_plan_outline_is_bounded():
    kernel = Build123dKernel()
    result = kernel.hlr_view(_box(kernel), direction=(0, 0, -1))
    xs = [p[0] for edge in result["visible"] for p in edge]
    ys = [p[1] for edge in result["visible"] for p in edge]
    # The plan view of the 30x20 top face spans 30 in one plane axis and 20 in the other; which
    # axis is which depends on the projection frame's up direction, so compare the sorted spans.
    spans = sorted([max(xs) - min(xs), max(ys) - min(ys)])
    assert spans[0] == pytest.approx(20, abs=1.0)
    assert spans[1] == pytest.approx(30, abs=1.0)


@pytest.mark.slow
def test_hlr_view_isometric_has_visible_and_hidden():
    kernel = Build123dKernel()
    result = kernel.hlr_view(_box(kernel), direction=(-1, -1, -1))  # iso: back edges are hidden
    assert result["visible"]
    assert result["hidden"], "an isometric view of a solid box hides its back edges"
