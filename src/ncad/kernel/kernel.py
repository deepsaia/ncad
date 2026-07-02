"""Abstract geometry-kernel contract.

The Builder talks only to this interface, never to a concrete backend, so the kernel
is swappable (build123d today, something else later) and Builder logic is testable
against a lightweight fake without importing a heavy CAD backend. Shapes are opaque
handles whose concrete type is the backend's business.

Coordinates and distances are in the document's canonical internal unit (millimetres).
"""

from abc import ABC, abstractmethod
from typing import Any

Point3 = tuple[float, float, float]
Point2 = tuple[float, float]
Bounds = tuple[Point3, Point3]


class Kernel(ABC):
    """Operations a geometry backend must provide for the general feature spine."""

    @abstractmethod
    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        """A closed planar face from ordered 2D ``points`` (not closed: first != last).

        ``plane`` is one of ``"XY"``, ``"XZ"``, ``"YZ"``; the 2D coordinates are placed
        on that plane through the world origin. Used to turn a solved sketch profile
        into a face for extrusion.
        """

    @abstractmethod
    def extrude(self, face: Any, distance: float) -> Any:
        """Extrude ``face`` along its normal by ``distance`` into a solid."""

    @abstractmethod
    def volume(self, solid: Any) -> float:
        """Volume of ``solid`` in cubic (internal-unit) units."""

    @abstractmethod
    def bounding_box(self, solid: Any) -> Bounds:
        """Axis-aligned bounds of ``solid`` as ``((minx,miny,minz),(maxx,maxy,maxz))``."""

    @abstractmethod
    def export(self, solid: Any, path: str) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension."""
