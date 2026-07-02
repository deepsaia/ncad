"""Contract tests for the trimmed Kernel, exercised through the fake kernel.

Fast: no OCP import. The real build123d kernel is tested (slow) separately.
"""

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
