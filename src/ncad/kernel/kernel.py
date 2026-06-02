"""Abstract geometry-kernel contract.

The Builder talks only to this interface, never to a concrete backend, so the kernel is
swappable (build123d today, something else later) and the Builder's logic is testable
against a lightweight fake without importing a heavy CAD backend. Solids are opaque
handles whose concrete type is the backend's business.
"""

from abc import ABC, abstractmethod
from typing import Any

Point3 = tuple[float, float, float]
Bounds = tuple[Point3, Point3]


class Kernel(ABC):
    """Operations a geometry backend must provide. Coordinates are meters, Z-up."""

    @abstractmethod
    def box(self, center: Point3, size: Point3) -> Any:
        """Create an axis-aligned box solid centered at ``center`` with extents ``size``."""

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
