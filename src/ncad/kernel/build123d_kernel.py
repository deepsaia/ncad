"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and exports to glTF / STEP /
STL. Importing this module pulls in OCP, which is slow on first load; keep it out of
the fast test path.
"""

import logging
from typing import Any

from build123d import (
    Axis,
    Edge,
    Face,
    Plane,
    Solid,
    Unit,
    Vector,
    Wire,
    export_gltf,
    export_step,
    export_stl,
    extrude,
)

from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3
from ncad.kernel.kernel_op_error import KernelOpError

logger = logging.getLogger(__name__)

_PLANES = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}
_AXES = {"X": Axis.X, "Y": Axis.Y, "Z": Axis.Z}


class Build123dKernel(Kernel):
    """build123d-backed kernel. Shapes are build123d ``Face``/``Solid`` objects."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane]
        world = [basis.from_local_coords(Vector(x, y, 0)) for x, y in points]
        closed = world + [world[0]]
        # build123d's from_local_coords is stubbed as a wide union; at runtime these are
        # Vectors, which make_line accepts. This is the untyped-OCP boundary (see the
        # [tool.pyrefly] note in pyproject); ignore rather than contort the code.
        edges = [
            Edge.make_line(closed[i], closed[i + 1])  # pyrefly: ignore[bad-argument-type]
            for i in range(len(world))
        ]
        return Face(Wire(edges))

    def extrude(self, face: Any, distance: float) -> Any:
        return extrude(face, amount=distance)

    def circle_face(self, center: Point2, diameter: float, plane: str) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane]
        # from_local_coords is stubbed as a wide union but returns a Vector at runtime;
        # this is the untyped-OCP boundary (see the [tool.pyrefly] note in pyproject).
        origin = basis.from_local_coords(Vector(center[0], center[1], 0))
        face_plane = Plane(origin=origin, z_dir=basis.z_dir)  # pyrefly: ignore[no-matching-overload]
        return Face(Wire(Edge.make_circle(diameter / 2.0, face_plane)))

    def cylinder(self, center: Point3, axis: str, diameter: float, length: float) -> Any:
        if axis not in _AXES:
            raise ValueError(f"axis must be one of {tuple(_AXES)}, got {axis!r}")
        base = Plane(origin=Vector(*center), z_dir=_AXES[axis].direction)
        return Solid.make_cylinder(diameter / 2.0, length, base)

    def cut(self, solid: Any, tools: list) -> Any:
        return self._robust(self._do_cut, solid, tools, name="cut")

    def fuse(self, solids: list) -> Any:
        return self._robust(self._do_fuse, solids, name="fuse")

    def intersect(self, solids: list) -> Any:
        return self._robust(self._do_intersect, solids, name="intersect")

    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        return self._robust(self._do_fillet, solid, edges, radius, name="fillet")

    def chamfer_edges(self, solid: Any, edges: list, distance: float) -> Any:
        return self._robust(self._do_chamfer, solid, edges, distance, name="chamfer")

    def edges_of(self, solid: Any) -> list:
        infos = []
        for e in solid.edges():
            p0, p1 = e.position_at(0), e.position_at(1)
            direction = p1 - p0
            vertical = (
                abs(direction.Z) > 1e-6 and abs(direction.X) < 1e-6 and abs(direction.Y) < 1e-6
            )
            infos.append({
                "edge": e,
                "orientation": "vertical" if vertical else "horizontal",
                "mid_z": e.position_at(0.5).Z,
            })
        return infos

    @staticmethod
    def _do_cut(solid: Any, tools: list) -> Any:
        result = solid
        for tool in tools:
            result = result - tool
        return result

    @staticmethod
    def _do_fuse(solids: list) -> Any:
        result = solids[0]
        for other in solids[1:]:
            result = result + other
        return result

    @staticmethod
    def _do_intersect(solids: list) -> Any:
        result = solids[0]
        for other in solids[1:]:
            result = result & other
        return result

    @staticmethod
    def _do_fillet(solid: Any, edges: list, radius: float) -> Any:
        return solid.fillet(radius, edges)

    @staticmethod
    def _do_chamfer(solid: Any, edges: list, distance: float) -> Any:
        return solid.chamfer(distance, None, edges)

    def _robust(self, op, *args, name: str) -> Any:
        """Run a fragile OCCT op and validate the result; raise KernelOpError on failure.

        Bucket 0.2 uses the validity-gate + typed-failure steps of the robustness ladder
        (docs/research/occt-boolean-robustness.md). Fuzzy-retry escalation and healing are
        a later hardening; the gate already converts silent OCCT failures into a typed
        error the calling op turns into an id-tagged issue.
        """
        try:
            result = op(*args)
        except Exception as exc:  # noqa: BLE001 - OCCT failures are broad; wrap them
            raise KernelOpError(f"{name} failed: {exc}") from exc
        if result is None or not self._is_valid(result):
            raise KernelOpError(f"{name} produced an invalid result")
        return result

    @staticmethod
    def _is_valid(shape: Any) -> bool:
        """Whether ``shape`` is a valid B-rep. ``is_valid`` is a property in build123d,
        but tolerate a callable form across versions."""
        flag = shape.is_valid
        return bool(flag() if callable(flag) else flag)

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
