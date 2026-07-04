"""Contract tests for the trimmed Kernel, exercised through the fake kernel.

Fast: no OCP import. The real build123d kernel is tested (slow) separately.
"""

import pytest

from tests.kernel.fake_kernel import FakeKernel


def test_extrude_rectangle_has_expected_volume() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    assert kernel.volume(solid) == 80.0 * 60.0 * 8.0


def test_extrude_rectangle_bounds() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == (0.0, 0.0, 0.0)
    assert (maxx, maxy, maxz) == (80.0, 60.0, 8.0)


def test_cut_reduces_volume() -> None:
    kernel = FakeKernel()
    block = kernel.extrude(kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY"), 8.0)
    tool = kernel.cylinder((10, 10, 0), "Z", 6.0, 8.0)

    result = kernel.cut(block, [tool])

    assert kernel.volume(result) < kernel.volume(block)


def test_fuse_adds_volume() -> None:
    kernel = FakeKernel()
    a = kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 5.0)
    b = kernel.extrude(kernel.polygon_face([(20, 0), (30, 0), (30, 10), (20, 10)], "XY"), 5.0)

    result = kernel.fuse([a, b])

    assert kernel.volume(result) == pytest.approx(1000.0)


def test_edges_of_classifies_orientation_and_z() -> None:
    kernel = FakeKernel()
    block = kernel.extrude(kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY"), 8.0)

    infos = kernel.edges_of(block)

    assert any(e["orientation"] == "vertical" for e in infos)
    assert any(e["orientation"] == "horizontal" for e in infos)
    assert max(e["mid_z"] for e in infos) == pytest.approx(8.0)


def test_fake_kernel_version_is_stable() -> None:
    assert FakeKernel().version() == "fake-1"


def test_fake_signature_of_box() -> None:
    kernel = FakeKernel()
    solid = kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 20), (0, 20)], "XY"), 5.0)

    sig = kernel.signature(solid)

    assert sig["counts"] == {"face": 6, "edge": 12, "vertex": 8}
    assert sig["surface_types"] == {"plane": 6}
    assert sig["volume"] == 10 * 20 * 5
    assert sig["bbox"] == ((0.0, 0.0, 0.0), (10.0, 20.0, 5.0))
    assert sig["cog"] == (5.0, 10.0, 2.5)


def test_fake_describe_elements_returns_faces_and_edges() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 20), (0, 20)], "XY")
    solid = kernel.extrude(face, 5.0)

    described = kernel.describe_elements(solid)

    faces = [d for d in described if d["kind"] == "face"]
    edges = [d for d in described if d["kind"] == "edge"]
    assert len(faces) == 6
    assert edges, "expected edge descriptors"
    top = [f for f in faces if f["normal"][2] == 1.0]
    assert top and top[0]["max_z"] == 5.0
    for descriptor in described:
        assert "center" in descriptor and "handle" in descriptor
