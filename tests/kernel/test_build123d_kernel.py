"""Slow tests for the real build123d kernel (imports OCP)."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel


@pytest.mark.slow
def test_extrude_rectangle_volume_is_exact() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    assert kernel.volume(solid) == pytest.approx(80.0 * 60.0 * 8.0)


@pytest.mark.slow
def test_extrude_rectangle_bounds_are_exact() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == pytest.approx((0.0, 0.0, 0.0))
    assert (maxx, maxy, maxz) == pytest.approx((80.0, 60.0, 8.0))


@pytest.mark.slow
def test_export_glb_writes_file(tmp_path) -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)

    out = tmp_path / "block.glb"
    kernel.export(solid, str(out))

    assert out.is_file() and out.stat().st_size > 0
