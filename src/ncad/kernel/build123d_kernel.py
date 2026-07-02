"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and exports to glTF / STEP /
STL. Importing this module pulls in OCP, which is slow on first load — keep it out of
the fast test path.
"""

import logging
from typing import Any

from build123d import (
    Edge,
    Face,
    Plane,
    Unit,
    Vector,
    Wire,
    export_gltf,
    export_step,
    export_stl,
    extrude,
)

from ncad.kernel.kernel import Bounds, Kernel, Point2

logger = logging.getLogger(__name__)

_PLANES = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}


class Build123dKernel(Kernel):
    """build123d-backed kernel. Shapes are build123d ``Face``/``Solid`` objects."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane]
        world = [basis.from_local_coords(Vector(x, y, 0)) for x, y in points]
        closed = world + [world[0]]
        edges = [Edge.make_line(closed[i], closed[i + 1]) for i in range(len(world))]
        return Face(Wire(edges))

    def extrude(self, face: Any, distance: float) -> Any:
        return extrude(face, amount=distance)

    def volume(self, solid: Any) -> float:
        return solid.volume

    def bounding_box(self, solid: Any) -> Bounds:
        box = solid.bounding_box()
        return (tuple(box.min), tuple(box.max))

    def export(self, solid: Any, path: str) -> None:
        lowered = path.lower()
        if lowered.endswith(".glb"):
            export_gltf(solid, path, unit=Unit.MM, binary=True)
        elif lowered.endswith(".gltf"):
            export_gltf(solid, path, unit=Unit.MM, binary=False)
        elif lowered.endswith((".step", ".stp")):
            export_step(solid, path, unit=Unit.MM)
        elif lowered.endswith(".stl"):
            export_stl(solid, path)
        else:
            raise ValueError(
                f"unsupported export format for {path!r}; expected .gltf/.glb/.step/.stp/.stl"
            )
        logger.debug("exported solid to %s", path)
