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
    """A cylinder tool: volume = pi r^2 * length; records its placement for assertions."""

    def __init__(self, center: Point3, axis: str, diameter: float, length: float) -> None:
        self.center = center
        self.axis = axis
        self.volume_val = math.pi * (diameter / 2.0) ** 2 * length


class _FakeCombined:
    """Result of a boolean or dress-up op: carries a computed volume and bounds.

    Downstream ops (a fillet after a hole, a chamfer after a union) still call
    ``edges_of``/``bounding_box`` on the result, so a combined shape must carry a
    bounding box, not just a volume.
    """

    def __init__(self, volume: float, bounds: Bounds) -> None:
        self.volume_val = volume
        self.bounds = bounds


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
        return _FakeCylinder(center, axis, diameter, length)

    def cut(self, solid: Any, tools: list) -> Any:
        # Cutting keeps the outer bounds of the solid being drilled/pocketed.
        return _FakeCombined(self.volume(solid) - sum(self.volume(t) for t in tools),
                             self.bounding_box(solid))

    def fuse(self, solids: list) -> Any:
        return _FakeCombined(sum(self.volume(s) for s in solids),
                             self._union_bounds(solids))

    def intersect(self, solids: list) -> Any:
        return _FakeCombined(min(self.volume(s) for s in solids),
                             self.bounding_box(solids[0]))

    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        return _FakeCombined(self.volume(solid) - radius * len(edges),
                             self.bounding_box(solid))

    def chamfer_edges(self, solid: Any, edges: list, distance: float) -> Any:
        return _FakeCombined(self.volume(solid) - distance * len(edges),
                             self.bounding_box(solid))

    def _union_bounds(self, solids: list) -> Bounds:
        """The bounding box enclosing all ``solids``."""
        boxes = [self.bounding_box(s) for s in solids]
        lows = [b[0] for b in boxes]
        highs = [b[1] for b in boxes]
        return (
            (min(p[0] for p in lows), min(p[1] for p in lows), min(p[2] for p in lows)),
            (max(p[0] for p in highs), max(p[1] for p in highs), max(p[2] for p in highs)),
        )

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

    def describe_elements(self, solid: Any) -> list:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        faces = [
            _box_face((minx + maxx) / 2, (miny + maxy) / 2, maxz, (0.0, 0.0, 1.0),
                      (maxx - minx) * (maxy - miny), maxz),
            _box_face((minx + maxx) / 2, (miny + maxy) / 2, minz, (0.0, 0.0, -1.0),
                      (maxx - minx) * (maxy - miny), minz),
            _box_face((minx + maxx) / 2, miny, (minz + maxz) / 2, (0.0, -1.0, 0.0),
                      (maxx - minx) * (maxz - minz), (minz + maxz) / 2),
            _box_face((minx + maxx) / 2, maxy, (minz + maxz) / 2, (0.0, 1.0, 0.0),
                      (maxx - minx) * (maxz - minz), (minz + maxz) / 2),
            _box_face(minx, (miny + maxy) / 2, (minz + maxz) / 2, (-1.0, 0.0, 0.0),
                      (maxy - miny) * (maxz - minz), (minz + maxz) / 2),
            _box_face(maxx, (miny + maxy) / 2, (minz + maxz) / 2, (1.0, 0.0, 0.0),
                      (maxy - miny) * (maxz - minz), (minz + maxz) / 2),
        ]
        edges = []
        for info in self.edges_of(solid):
            edges.append({
                "kind": "edge", "handle": info["edge"], "geom_type": "line",
                "length": 0.0, "center": (0.0, 0.0, info["mid_z"]),
                "orientation": info["orientation"],
                "min_z": info["mid_z"], "mid_z": info["mid_z"], "max_z": info["mid_z"],
            })
        return faces + edges

    def version(self) -> str:
        return "fake-1"

    def signature(self, solid: Any) -> dict:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        dx, dy, dz = maxx - minx, maxy - miny, maxz - minz
        area = 2.0 * (dx * dy + dy * dz + dx * dz)
        return {
            "counts": {"face": 6, "edge": 12, "vertex": 8},
            "surface_types": {"plane": 6},
            "curve_types": {"line": 12},
            "volume": self.volume(solid),
            "area": area,
            "bbox": ((minx, miny, minz), (maxx, maxy, maxz)),
            "cog": ((minx + maxx) / 2, (miny + maxy) / 2, (minz + maxz) / 2),
        }

    def volume(self, solid: Any) -> float:
        if isinstance(solid, (_FakeCylinder, _FakeCombined)):
            return solid.volume_val
        return _polygon_area(solid.face.points) * solid.distance

    def bounding_box(self, solid: Any) -> Bounds:
        if isinstance(solid, _FakeCombined):
            return solid.bounds
        xs = [x for x, _ in solid.face.points]
        ys = [y for _, y in solid.face.points]
        # Bucket 0.1 uses the XY plane; extrude along +Z by distance.
        return ((min(xs), min(ys), 0.0), (max(xs), max(ys), solid.distance))

    def export(self, solid: Any, path: str) -> None:
        raise NotImplementedError("FakeKernel does not export geometry")


def _box_face(cx: float, cy: float, cz: float, normal: Point3, area: float,
              z: float) -> dict:
    """A synthetic planar face descriptor for the FakeKernel's axis-aligned bounds."""
    return {
        "kind": "face", "handle": object(), "geom_type": "planar", "normal": normal,
        "area": area, "center": (cx, cy, cz), "min_z": z, "mid_z": z, "max_z": z,
    }


def _polygon_area(points: list[Point2]) -> float:
    """Shoelace area of a closed ring given as non-repeating vertices."""
    n = len(points)
    total = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0
