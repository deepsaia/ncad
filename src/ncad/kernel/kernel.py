"""Abstract geometry-kernel contract.

The Builder talks only to this interface, never to a concrete backend, so the kernel is
swappable (build123d today, something else later) and the Builder's logic is testable
against a lightweight fake without importing a heavy CAD backend. Solids are opaque
handles whose concrete type is the backend's business.
"""

from abc import ABC, abstractmethod
from typing import Any

Point3 = tuple[float, float, float]
Point2 = tuple[float, float]
Bounds = tuple[Point3, Point3]


class Kernel(ABC):
    """Operations a geometry backend must provide. Coordinates are meters, Z-up."""

    @abstractmethod
    def box(self, center: Point3, size: Point3) -> Any:
        """Create an axis-aligned box solid centered at ``center`` with extents ``size``."""

    @abstractmethod
    def prism(self, profile: list[Point2], axis: str, start: float, end: float) -> Any:
        """Extrude a vertical 2D cross-section into a horizontal prism.

        Used for pitched roofs (gable triangle, shed wedge). The ``profile`` is a list of
        ``(cross, z)`` points in the vertical plane perpendicular to ``axis``, where
        ``cross`` is the world coordinate on the non-extrusion horizontal axis and ``z``
        is elevation. The profile is extruded along ``axis`` (``"x"`` or ``"y"``) from
        ``start`` to ``end`` (world coordinates on that axis).
        """

    @abstractmethod
    def extrude_polygon(self, polygon: list[Point2], base_z: float, height: float) -> Any:
        """Extrude a horizontal 2D polygon vertically into a prism.

        Used for slabs and flat roofs over arbitrary (e.g. L/T/U) footprints. The
        ``polygon`` is an ordered list of ``(x, y)`` boundary vertices in meters, not
        closed (first != last). The solid spans ``base_z`` to ``base_z + height``.
        Distinct from :meth:`prism`, which extrudes a vertical cross-section horizontally.
        """

    @abstractmethod
    def extrude_rounded_polygon(
        self, polygon: list[Point2], corner_radii: dict[int, float], base_z: float, height: float
    ) -> Any:
        """Extrude a polygon with selected corners rounded (filleted), then extruded up.

        Like :meth:`extrude_polygon`, but ``corner_radii`` maps a vertex index to a fillet
        radius; vertices not present (or radius 0) stay sharp. Used for rounded footprint
        slabs/roofs. ``corner_radii == {}`` is equivalent to :meth:`extrude_polygon`.
        """

    @abstractmethod
    def arc_wall(
        self,
        center: Point2,
        radius: float,
        start_angle: float,
        end_angle: float,
        base_z: float,
        height: float,
        thickness: float,
    ) -> Any:
        """A curved wall: an annular sector (band of width ``thickness`` centered on
        ``radius``) about ``center``, swept from ``start_angle`` to ``end_angle`` (degrees),
        extruded vertically from ``base_z`` by ``height``. Used for walls turning a rounded
        corner.
        """

    @abstractmethod
    def sphere(self, center: Point3, radius: float) -> Any:
        """A solid sphere of ``radius`` centered at ``center``. Used for dome corners."""

    @abstractmethod
    def barrel(self, start: Point2, end: Point2, radius: float, base_z: float) -> Any:
        """A horizontal half-cylinder vault: the top half of a cylinder of ``radius`` whose
        axis runs along the segment ``start``->``end`` at height ``base_z``. The flat cut is
        at ``base_z`` (vault sits on the wall); the crown reaches ``base_z + radius``. Used
        for dome edges.
        """

    @abstractmethod
    def intersect(self, solids: list[Any]) -> Any:
        """Boolean-intersect a non-empty list of solids (the common volume)."""

    @abstractmethod
    def union(self, solids: list[Any]) -> Any:
        """Boolean-union a non-empty list of solids into one."""

    @abstractmethod
    def subtract(self, solid: Any, tools: list[Any]) -> Any:
        """Boolean-subtract each tool solid from ``solid``."""

    @abstractmethod
    def volume(self, solid: Any) -> float:
        """Volume of ``solid`` in cubic meters."""

    @abstractmethod
    def bounding_box(self, solid: Any) -> Bounds:
        """Axis-aligned bounds of ``solid`` as ``((minx,miny,minz),(maxx,maxy,maxz))``."""

    @abstractmethod
    def export(self, solid: Any, path: str) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension."""
