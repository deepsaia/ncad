"""A lightweight, dependency-free Kernel for fast tests.

A face is modeled as its 2D point ring plus plane; a solid as (face, distance). Volume
and bounds are computed analytically for the axis-aligned extrusion cases the buckets
use. Boolean/fillet results carry a computed volume only. Not for production geometry;
enough to assert op and Builder behaviour without OCP.
"""

import math
from typing import Any

from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3


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


class _FakeCylinder:
    """A cylinder tool: volume = pi r^2 * length."""

    def __init__(self, diameter: float, length: float) -> None:
        self.volume_val = math.pi * (diameter / 2.0) ** 2 * length


class _FakeCombined:
    """Result of a boolean or dress-up op: carries a computed volume only."""

    def __init__(self, volume: float) -> None:
        self.volume_val = volume


class FakeKernel(Kernel):
    """In-memory kernel: analytic volume/bounds for axis-aligned extrusions."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        return _FakeFace(points, plane)

    def extrude(self, face: Any, distance: float) -> Any:
        return _FakeSolid(face, distance)

    def circle_face(self, center: Point2, diameter: float, plane: str) -> Any:
        cx, cy = center
        r = diameter / 2.0
        pts = [(cx + r * math.cos(2 * math.pi * i / 48), cy + r * math.sin(2 * math.pi * i / 48))
               for i in range(48)]
        return _FakeFace(pts, plane)

    def cylinder(self, center: Point3, axis: str, diameter: float, length: float) -> Any:
        return _FakeCylinder(diameter, length)

    def cut(self, solid: Any, tools: list) -> Any:
        return _FakeCombined(self.volume(solid) - sum(self.volume(t) for t in tools))

    def fuse(self, solids: list) -> Any:
        return _FakeCombined(sum(self.volume(s) for s in solids))

    def intersect(self, solids: list) -> Any:
        return _FakeCombined(min(self.volume(s) for s in solids))

    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        return _FakeCombined(self.volume(solid) - radius * len(edges))

    def chamfer_edges(self, solid: Any, edges: list, distance: float) -> Any:
        return _FakeCombined(self.volume(solid) - distance * len(edges))

    def edges_of(self, solid: Any) -> list:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        infos = []
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "vertical",
                          "mid_z": (minz + maxz) / 2})
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "horizontal", "mid_z": maxz})
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "horizontal", "mid_z": minz})
        return infos

    def volume(self, solid: Any) -> float:
        if isinstance(solid, (_FakeCylinder, _FakeCombined)):
            return solid.volume_val
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
