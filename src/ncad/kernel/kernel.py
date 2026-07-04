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
    def circle_face(self, center: Point2, diameter: float, plane: str) -> Any:
        """A circular planar face of ``diameter`` centred at ``center`` on ``plane``."""

    @abstractmethod
    def cylinder(self, center: Point3, axis: str, diameter: float, length: float) -> Any:
        """A solid cylinder of ``diameter`` and ``length`` from ``center`` along ``axis``."""

    @abstractmethod
    def cut(self, solid: Any, tools: list) -> Any:
        """Subtract each tool in ``tools`` from ``solid``."""

    @abstractmethod
    def fuse(self, solids: list) -> Any:
        """Union a non-empty list of solids into one."""

    @abstractmethod
    def intersect(self, solids: list) -> Any:
        """Intersect a non-empty list of solids (their common volume)."""

    @abstractmethod
    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        """Round the given ``edges`` of ``solid`` with ``radius``."""

    @abstractmethod
    def chamfer_edges(self, solid: Any, edges: list, distance: float) -> Any:
        """Bevel the given ``edges`` of ``solid`` by ``distance``."""

    @abstractmethod
    def edges_of(self, solid: Any) -> list:
        """List edge descriptors ``{"edge", "orientation", "mid_z"}`` for ``solid``."""

    @abstractmethod
    def describe_elements(self, solid: Any) -> list:
        """Describe the faces and edges of ``solid`` for the reference model.

        Returns face descriptors first (in the backend's native face order, which the
        glTF exporter mirrors as mesh-part order), then edge descriptors. Face dict:
        ``{"kind":"face","handle","geom_type","normal","area","center","min_z","mid_z",
        "max_z"}``. Edge dict: ``{"kind":"edge","handle","geom_type","length","center",
        "orientation","min_z","mid_z","max_z"}``.
        """

    @abstractmethod
    def version(self) -> str:
        """A stable identifier for the pinned kernel build.

        Baked into cache keys (design section 4a) so a kernel/dependency bump
        invalidates cached geometry wholesale.
        """

    @abstractmethod
    def signature(self, solid: Any) -> dict:
        """The equality tuple for ``solid`` (design section 4a).

        ``{"counts": {"face","edge","vertex": int}, "surface_types": {name: int},
        "curve_types": {name: int}, "volume": float, "area": float,
        "bbox": ((minx,miny,minz),(maxx,maxy,maxz)), "cog": (x,y,z)}``. Topology
        counts/types are exact; measures are compared under a tolerance by the
        EqualityComparator.
        """

    @abstractmethod
    def volume(self, solid: Any) -> float:
        """Volume of ``solid`` in cubic (internal-unit) units."""

    @abstractmethod
    def bounding_box(self, solid: Any) -> Bounds:
        """Axis-aligned bounds of ``solid`` as ``((minx,miny,minz),(maxx,maxy,maxz))``."""

    @abstractmethod
    def export(self, solid: Any, path: str) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension."""
