"""A lightweight, dependency-free Kernel for fast tests.

A face is modeled as its 2D point ring plus plane; a solid as (face, distance). Volume
and bounds are computed analytically for the axis-aligned extrusion cases Bucket 0.1
uses. Not for production geometry — enough to assert Builder behaviour without OCP.
"""

from typing import Any

from ncad.kernel.kernel import Bounds, Kernel, Point2


class _FakeFace:
    """A planar polygon: its 2D point ring and the plane it lives on."""

    def __init__(self, points: list[Point2], plane: str) -> None:
        self.points = points
        self.plane = plane


class _FakeSolid:
    """A face extruded by a distance along the plane normal."""

    def __init__(self, face: _FakeFace, distance: float) -> None:
        self.face = face
        self.distance = distance


class FakeKernel(Kernel):
    """In-memory kernel: analytic volume/bounds for axis-aligned extrusions."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        return _FakeFace(points, plane)

    def extrude(self, face: Any, distance: float) -> Any:
        return _FakeSolid(face, distance)

    def volume(self, solid: Any) -> float:
        return _polygon_area(solid.face.points) * solid.distance

    def bounding_box(self, solid: Any) -> Bounds:
        xs = [x for x, _ in solid.face.points]
        ys = [y for _, y in solid.face.points]
        # Bucket 0.1 uses the XY plane; extrude along +Z by distance.
        return ((min(xs), min(ys), 0.0), (max(xs), max(ys), solid.distance))

    def export(self, solid: Any, path: str) -> None:
        raise NotImplementedError("FakeKernel does not export geometry")


def _polygon_area(points: list[Point2]) -> float:
    """Shoelace area of a closed ring given as non-repeating vertices."""
    n = len(points)
    total = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0
