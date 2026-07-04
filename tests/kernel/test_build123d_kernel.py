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


@pytest.mark.slow
def test_cut_and_fillet_on_real_kernel() -> None:
    kernel = Build123dKernel()
    block = kernel.extrude(kernel.polygon_face([(0, 0), (40, 0), (40, 30), (0, 30)], "XY"), 8.0)
    tool = kernel.cylinder((10, 10, 0), "Z", 6.0, 8.0)

    drilled = kernel.cut(block, [tool])
    assert kernel.volume(drilled) < kernel.volume(block)

    vertical = [e["edge"] for e in kernel.edges_of(drilled) if e["orientation"] == "vertical"]
    rounded = kernel.fillet_edges(drilled, vertical[:4], 2.0)
    assert rounded is not None


@pytest.mark.slow
def test_describe_elements_lists_six_box_faces_in_face_order() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 20), (0, 20)], "XY")
    solid = kernel.extrude(face, 5.0)

    described = kernel.describe_elements(solid)
    faces = [d for d in described if d["kind"] == "face"]
    assert len(faces) == 6
    assert [round(f["center"][2], 3) for f in faces] == \
        [round(g.center().Z, 3) for g in solid.faces()]
    top = [f for f in faces if round(f["normal"][2], 3) == 1.0]
    assert top and round(top[0]["max_z"], 3) == 5.0
