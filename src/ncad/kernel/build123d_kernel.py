"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and boolean operations, and
exports to glTF / STEP / STL. Exports are written in **meters** to match the spec's
units (build123d defaults to millimeters). Importing this module pulls in OCP, which is
slow on first load — keep it out of the fast test path.
"""

import logging
import math
from typing import Any

from build123d import (
    Box,
    Edge,
    Face,
    Pos,
    Unit,
    Vector,
    Wire,
    export_gltf,
    export_step,
    export_stl,
    extrude,
)

from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3

logger = logging.getLogger(__name__)

_ARC_SEGMENTS = 12  # segments approximating each rounded-corner arc
_ARC_BAND_SEGMENTS = 16  # segments approximating an arc wall's annular band


class Build123dKernel(Kernel):
    """build123d-backed kernel. Solids are build123d ``Solid``/``Compound`` objects."""

    def box(self, center: Point3, size: Point3) -> Any:
        cx, cy, cz = center
        sx, sy, sz = size
        return Pos(cx, cy, cz) * Box(sx, sy, sz)

    def prism(self, profile: list[Point2], axis: str, start: float, end: float) -> Any:
        lo, length = min(start, end), abs(end - start)
        if axis == "x":
            points = [Vector(lo, cross, z) for cross, z in profile]
            direction = Vector(1, 0, 0)
        elif axis == "y":
            points = [Vector(cross, lo, z) for cross, z in profile]
            direction = Vector(0, 1, 0)
        else:
            raise ValueError(f"prism axis must be 'x' or 'y', got {axis!r}")
        closed = points + [points[0]]
        edges = [Edge.make_line(closed[i], closed[i + 1]) for i in range(len(points))]
        face = Face(Wire(edges))
        return extrude(face, amount=length, dir=direction)

    def extrude_polygon(self, polygon: list[Point2], base_z: float, height: float) -> Any:
        points = [Vector(x, y, base_z) for x, y in polygon]
        closed = points + [points[0]]
        edges = [Edge.make_line(closed[i], closed[i + 1]) for i in range(len(points))]
        face = Face(Wire(edges))
        return extrude(face, amount=height, dir=Vector(0, 0, 1))

    def extrude_rounded_polygon(
        self, polygon: list[Point2], corner_radii: dict[int, float], base_z: float, height: float
    ) -> Any:
        rounded = _round_corners(polygon, corner_radii)
        return self.extrude_polygon(rounded, base_z, height)

    def arc_wall(
        self, center, radius, start_angle, end_angle, base_z, height, thickness
    ) -> Any:
        band = _annular_band(center, radius, start_angle, end_angle, thickness)
        return self.extrude_polygon(band, base_z, height)

    def union(self, solids: list[Any]) -> Any:
        if not solids:
            raise ValueError("union requires at least one solid")
        result = solids[0]
        for solid in solids[1:]:
            result = result + solid
        return result

    def subtract(self, solid: Any, tools: list[Any]) -> Any:
        result = solid
        for tool in tools:
            result = result - tool
        return result

    def volume(self, solid: Any) -> float:
        return solid.volume

    def bounding_box(self, solid: Any) -> Bounds:
        box = solid.bounding_box()
        return (tuple(box.min), tuple(box.max))

    def export(self, solid: Any, path: str) -> None:
        lowered = path.lower()
        if lowered.endswith(".glb"):
            # Binary glTF: a single self-contained file (no external .bin sidecar).
            export_gltf(solid, path, unit=Unit.M, binary=True)
        elif lowered.endswith(".gltf"):
            # Text glTF writes a companion <name>.bin buffer alongside the .gltf.
            export_gltf(solid, path, unit=Unit.M, binary=False)
        elif lowered.endswith(".step") or lowered.endswith(".stp"):
            export_step(solid, path, unit=Unit.M)
        elif lowered.endswith(".stl"):
            export_stl(solid, path)
        else:
            raise ValueError(
                f"unsupported export format for {path!r}; expected .gltf/.glb/.step/.stp/.stl"
            )
        logger.debug("exported solid to %s", path)


def _round_corners(polygon: list[Point2], corner_radii: dict[int, float]) -> list[Point2]:
    """Replace each radius'd corner with points sampled along its true fillet arc."""
    n = len(polygon)
    out: list[Point2] = []
    for i in range(n):
        radius = corner_radii.get(i, 0.0)
        if radius <= 0:
            out.append(polygon[i])
            continue
        prev_pt, corner, next_pt = polygon[(i - 1) % n], polygon[i], polygon[(i + 1) % n]
        out.extend(_arc_points(prev_pt, corner, next_pt, radius))
    return out


def _annular_band(center, radius, start_angle, end_angle, thickness) -> list[Point2]:
    """Closed polygon for an annular sector along the MINOR arc between the two angles."""
    cx, cy = center
    a0 = math.radians(start_angle)
    a1 = math.radians(end_angle)
    # A fillet is always the minor arc — normalize the span to |Δ| <= pi.
    while a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    while a1 - a0 < -math.pi:
        a1 += 2 * math.pi
    r_out, r_in = radius + thickness / 2, radius - thickness / 2
    outer, inner = [], []
    for s in range(_ARC_BAND_SEGMENTS + 1):
        t = s / _ARC_BAND_SEGMENTS
        ang = a0 + (a1 - a0) * t
        outer.append((cx + r_out * math.cos(ang), cy + r_out * math.sin(ang)))
        inner.append((cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)))
    return outer + list(reversed(inner))


def _arc_points(prev_pt, corner, next_pt, radius) -> list[Point2]:
    """Sample the inscribed fillet arc at ``corner`` tangent to both adjacent edges."""
    cx, cy = corner
    v_in = (prev_pt[0] - cx, prev_pt[1] - cy)
    v_out = (next_pt[0] - cx, next_pt[1] - cy)
    in_len = math.hypot(*v_in) or 1.0
    out_len = math.hypot(*v_out) or 1.0
    u_in = (v_in[0] / in_len, v_in[1] / in_len)
    u_out = (v_out[0] / out_len, v_out[1] / out_len)
    cos_full = max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1]))
    half = math.acos(cos_full) / 2.0
    if half <= 1e-6:
        return [corner]
    setback = radius / math.tan(half)
    tan_in = (cx + u_in[0] * setback, cy + u_in[1] * setback)
    tan_out = (cx + u_out[0] * setback, cy + u_out[1] * setback)
    # Arc center: along the bisector, at distance radius / sin(half) from the corner.
    bisector = (u_in[0] + u_out[0], u_in[1] + u_out[1])
    blen = math.hypot(*bisector) or 1.0
    center_dist = radius / math.sin(half)
    center = (cx + bisector[0] / blen * center_dist, cy + bisector[1] / blen * center_dist)
    start_ang = math.atan2(tan_in[1] - center[1], tan_in[0] - center[0])
    end_ang = math.atan2(tan_out[1] - center[1], tan_out[0] - center[0])
    # Take the short way around.
    while end_ang - start_ang > math.pi:
        end_ang -= 2 * math.pi
    while end_ang - start_ang < -math.pi:
        end_ang += 2 * math.pi
    points = []
    for s in range(_ARC_SEGMENTS + 1):
        t = s / _ARC_SEGMENTS
        ang = start_ang + (end_ang - start_ang) * t
        points.append((center[0] + radius * math.cos(ang), center[1] + radius * math.sin(ang)))
    return points
