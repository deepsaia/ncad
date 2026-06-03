"""A lightweight, dependency-free Kernel for fast Builder tests.

A solid is modeled as a constructive list of (box, is_additive) terms. Volume and bounds
are computed by deterministic point sampling over the combined bounding region — exact
enough to assert builder behavior (counts, relative volumes, openings reducing volume)
without importing the OCP backend. Not for production geometry.
"""

from typing import Any

from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3

_SAMPLES_PER_AXIS = 40


class _Box:
    """An axis-aligned box, min/max corners in meters."""

    def __init__(self, center: Point3, size: Point3) -> None:
        cx, cy, cz = center
        sx, sy, sz = size
        self.min = (cx - sx / 2, cy - sy / 2, cz - sz / 2)
        self.max = (cx + sx / 2, cy + sy / 2, cz + sz / 2)

    def contains(self, x: float, y: float, z: float) -> bool:
        return (
            self.min[0] <= x <= self.max[0]
            and self.min[1] <= y <= self.max[1]
            and self.min[2] <= z <= self.max[2]
        )


class _Prism:
    """A vertical 2D profile (cross, z) extruded along a horizontal axis."""

    def __init__(self, profile: list[Point2], axis: str, start: float, end: float) -> None:
        self._profile = profile
        self._axis = axis
        self._lo, self._hi = (start, end) if start <= end else (end, start)
        crosses = [p[0] for p in profile]
        zs = [p[1] for p in profile]
        cmin, cmax, zmin, zmax = min(crosses), max(crosses), min(zs), max(zs)
        if axis == "x":  # extrude along x; cross-section spans y/z
            self.min = (self._lo, cmin, zmin)
            self.max = (self._hi, cmax, zmax)
        else:  # axis == "y"; cross-section spans x/z
            self.min = (cmin, self._lo, zmin)
            self.max = (cmax, self._hi, zmax)

    def contains(self, x: float, y: float, z: float) -> bool:
        if self._axis == "x":
            if not self._lo <= x <= self._hi:
                return False
            return _point_in_polygon(y, z, self._profile)
        if not self._lo <= y <= self._hi:
            return False
        return _point_in_polygon(x, z, self._profile)


class _PolygonPrism:
    """A horizontal 2D polygon extruded vertically from base_z to base_z + height."""

    def __init__(self, polygon: list[Point2], base_z: float, height: float) -> None:
        self._polygon = polygon
        self._base_z = base_z
        self._top_z = base_z + height
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        self.min = (min(xs), min(ys), base_z)
        self.max = (max(xs), max(ys), self._top_z)

    def contains(self, x: float, y: float, z: float) -> bool:
        if not self._base_z <= z <= self._top_z:
            return False
        return _point_in_polygon(x, y, self._polygon)


class _Solid:
    """A CSG expression: additive boxes minus subtractive ones."""

    def __init__(self, additive: list[_Box], subtractive: list[_Box]) -> None:
        self.additive = additive
        self.subtractive = subtractive


class FakeKernel(Kernel):
    """In-memory Kernel that approximates volume/bounds by sampling."""

    def box(self, center: Point3, size: Point3) -> Any:
        return _Solid(additive=[_Box(center, size)], subtractive=[])

    def prism(self, profile: list[Point2], axis: str, start: float, end: float) -> Any:
        return _Solid(additive=[_Prism(profile, axis, start, end)], subtractive=[])

    def extrude_polygon(self, polygon: list[Point2], base_z: float, height: float) -> Any:
        return _Solid(additive=[_PolygonPrism(polygon, base_z, height)], subtractive=[])

    def union(self, solids: list[Any]) -> Any:
        additive: list[_Box] = []
        subtractive: list[_Box] = []
        for solid in solids:
            additive.extend(solid.additive)
            subtractive.extend(solid.subtractive)
        return _Solid(additive, subtractive)

    def subtract(self, solid: Any, tools: list[Any]) -> Any:
        tool_boxes: list[_Box] = []
        for tool in tools:
            tool_boxes.extend(tool.additive)
        return _Solid(solid.additive, solid.subtractive + tool_boxes)

    def volume(self, solid: Any) -> float:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        if minx >= maxx or miny >= maxy or minz >= maxz:
            return 0.0
        # Exact for axis-aligned, non-overlapping boxes (our wall/opening case): sum of
        # additive box volumes minus subtractive overlap, computed by sampling.
        n = _SAMPLES_PER_AXIS
        dx, dy, dz = (maxx - minx) / n, (maxy - miny) / n, (maxz - minz) / n
        cell = dx * dy * dz
        inside = 0
        for i in range(n):
            x = minx + (i + 0.5) * dx
            for j in range(n):
                y = miny + (j + 0.5) * dy
                for k in range(n):
                    z = minz + (k + 0.5) * dz
                    if self._point_inside(solid, x, y, z):
                        inside += 1
        return inside * cell

    def bounding_box(self, solid: Any) -> Bounds:
        boxes = solid.additive
        mins = [b.min for b in boxes]
        maxs = [b.max for b in boxes]
        return (
            (min(m[0] for m in mins), min(m[1] for m in mins), min(m[2] for m in mins)),
            (max(m[0] for m in maxs), max(m[1] for m in maxs), max(m[2] for m in maxs)),
        )

    def export(self, solid: Any, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(f"fake solid: vol={self.volume(solid):.4f}\n")

    def _point_inside(self, solid: _Solid, x: float, y: float, z: float) -> bool:
        in_additive = any(shape.contains(x, y, z) for shape in solid.additive)
        if not in_additive:
            return False
        return not any(shape.contains(x, y, z) for shape in solid.subtractive)


def _point_in_polygon(u: float, v: float, polygon: list[Point2]) -> bool:
    """Ray-casting point-in-polygon test for a 2D (u, v) point."""
    inside = False
    count = len(polygon)
    j = count - 1
    for i in range(count):
        ui, vi = polygon[i]
        uj, vj = polygon[j]
        if (vi > v) != (vj > v):
            slope_u = ui + (v - vi) / (vj - vi) * (uj - ui)
            if u < slope_u:
                inside = not inside
        j = i
    return inside
