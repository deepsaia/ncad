"""A lightweight, dependency-free Kernel for fast Builder tests.

A solid is modeled as a constructive list of (box, is_additive) terms. Volume and bounds
are computed by deterministic point sampling over the combined bounding region — exact
enough to assert builder behavior (counts, relative volumes, openings reducing volume)
without importing the OCP backend. Not for production geometry.
"""

import math
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

    def extrude_rounded_polygon(
        self, polygon: list[Point2], corner_radii: dict[int, float], base_z: float, height: float
    ) -> Any:
        rounded = _round_corners(polygon, corner_radii)
        return _Solid(additive=[_PolygonPrism(rounded, base_z, height)], subtractive=[])

    def arc_wall(
        self, center, radius, start_angle, end_angle, base_z, height, thickness
    ) -> Any:
        band = _annular_band(center, radius, start_angle, end_angle, thickness)
        return _Solid(additive=[_PolygonPrism(band, base_z, height)], subtractive=[])

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


_FILLET_SEGMENTS = 8  # chord segments approximating each rounded corner


def _round_corners(polygon: list[Point2], corner_radii: dict[int, float]) -> list[Point2]:
    """Replace each radius'd corner with chord segments along an inscribed fillet arc.

    Mirrors a CAD fillet: the arc is tangent to both edges at distance ``r / tan(half)``
    from the corner. Sharp corners (no radius) are passed through unchanged.
    """
    n = len(polygon)
    out: list[Point2] = []
    for i in range(n):
        radius = corner_radii.get(i, 0.0)
        if radius <= 0:
            out.append(polygon[i])
            continue
        prev_pt, corner, next_pt = polygon[(i - 1) % n], polygon[i], polygon[(i + 1) % n]
        out.extend(_fillet_points(prev_pt, corner, next_pt, radius))
    return out


def _fillet_points(prev_pt, corner, next_pt, radius) -> list[Point2]:
    cx, cy = corner
    v_in = (prev_pt[0] - cx, prev_pt[1] - cy)
    v_out = (next_pt[0] - cx, next_pt[1] - cy)
    in_len = math.hypot(*v_in) or 1.0
    out_len = math.hypot(*v_out) or 1.0
    u_in = (v_in[0] / in_len, v_in[1] / in_len)
    u_out = (v_out[0] / out_len, v_out[1] / out_len)
    half = math.acos(max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))) / 2.0
    if half <= 1e-6:
        return [corner]
    setback = radius / math.tan(half)
    tan_in = (cx + u_in[0] * setback, cy + u_in[1] * setback)
    tan_out = (cx + u_out[0] * setback, cy + u_out[1] * setback)
    # Sample the straight chord between the two tangent points (a coarse arc approximation
    # that is provably inside the true fillet, so the fake stays conservative).
    points = []
    for s in range(_FILLET_SEGMENTS + 1):
        t = s / _FILLET_SEGMENTS
        points.append((tan_in[0] + (tan_out[0] - tan_in[0]) * t,
                       tan_in[1] + (tan_out[1] - tan_in[1]) * t))
    return points


_ARC_BAND_SEGMENTS = 16  # segments approximating an arc wall's annular band


def _annular_band(center, radius, start_angle, end_angle, thickness) -> list[Point2]:
    """Closed polygon for an annular sector along the MINOR arc between the two angles."""
    cx, cy = center
    a0 = math.radians(start_angle)
    a1 = math.radians(end_angle)
    while a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    while a1 - a0 < -math.pi:
        a1 += 2 * math.pi
    r_out, r_in = radius + thickness / 2, radius - thickness / 2
    outer = []
    inner = []
    for s in range(_ARC_BAND_SEGMENTS + 1):
        t = s / _ARC_BAND_SEGMENTS
        ang = a0 + (a1 - a0) * t
        outer.append((cx + r_out * math.cos(ang), cy + r_out * math.sin(ang)))
        inner.append((cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)))
    return outer + list(reversed(inner))


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
