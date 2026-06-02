"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and boolean operations, and
exports to glTF / STEP / STL. Exports are written in **meters** to match the spec's
units (build123d defaults to millimeters). Importing this module pulls in OCP, which is
slow on first load — keep it out of the fast test path.
"""

import logging
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
