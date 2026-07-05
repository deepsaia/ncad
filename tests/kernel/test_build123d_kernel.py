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


@pytest.mark.slow
def test_version_reports_build123d_and_ocp() -> None:
    v = Build123dKernel().version()
    assert v.startswith("build123d=") and "ocp=" in v


@pytest.mark.slow
def test_signature_of_box_is_correct() -> None:
    kernel = Build123dKernel()
    solid = kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 20), (0, 20)], "XY"), 5.0)

    sig = kernel.signature(solid)

    assert sig["counts"] == {"face": 6, "edge": 12, "vertex": 8}
    assert sig["surface_types"] == {"plane": 6}
    assert sig["volume"] == pytest.approx(10 * 20 * 5)
    assert sig["cog"] == pytest.approx((5.0, 10.0, 2.5))


@pytest.mark.slow
def test_wire_face_mixed_line_and_arc_is_valid() -> None:
    kernel = Build123dKernel()
    edges = [
        {"kind": "line", "points": [(0.0, 0.0), (20.0, 0.0)]},
        {"kind": "arc", "points": [(20.0, 0.0), (25.0, 5.0), (20.0, 10.0)]},
        {"kind": "line", "points": [(20.0, 10.0), (0.0, 10.0)]},
        {"kind": "line", "points": [(0.0, 10.0), (0.0, 0.0)]},
    ]
    solid = kernel.extrude(kernel.wire_face(edges, "XY"), 5.0)
    assert kernel.volume(solid) > 0


@pytest.mark.slow
def test_wire_face_circle_is_valid() -> None:
    import math

    kernel = Build123dKernel()
    solid = kernel.extrude(
        kernel.wire_face([{"kind": "circle", "center": (0.0, 0.0), "radius": 6.0}], "XY"), 3.0)
    assert kernel.volume(solid) == pytest.approx(math.pi * 36.0 * 3.0, rel=1e-3)


@pytest.mark.slow
def test_project_edges_of_a_top_face_gives_rectangle() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (20, 0), (20, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)
    top_edges = [d["handle"] for d in kernel.describe_elements(solid)
                 if d["kind"] == "edge" and round(d["max_z"], 3) == 5.0]
    projected = kernel.project_edges(top_edges, "XY")
    lines = [p for p in projected if p["kind"] == "line"]
    assert lines, "top rectangle edges should project to lines"
    xs = [pt[0] for p in lines for pt in p["points"]]
    ys = [pt[1] for p in lines for pt in p["points"]]
    assert min(xs) == pytest.approx(0.0) and max(xs) == pytest.approx(20.0)
    assert min(ys) == pytest.approx(0.0) and max(ys) == pytest.approx(10.0)
