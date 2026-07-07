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
    def polygon_face(self, points: list[Point2], plane: str, offset: float = 0.0) -> Any:
        """A closed planar face from ordered 2D ``points`` (not closed: first != last).

        ``plane`` is one of ``"XY"``, ``"XZ"``, ``"YZ"``; ``offset`` shifts that plane along
        its normal by that signed distance (default 0.0 = through the world origin). Used to
        turn a solved sketch profile into a face for extrusion or a loft section.
        """

    @abstractmethod
    def extrude(self, face: Any, distance: float | None = None, *,
                symmetric: bool = False, second_distance: float | None = None,
                draft: float = 0.0, thin: float | None = None,
                until: str | None = None, target: Any = None) -> Any:
        """Extrude ``face`` into a solid.

        ``distance`` blind along the normal; ``symmetric`` centers that total distance on
        the face plane; ``second_distance`` adds a second extrude the other way (fused);
        ``draft`` tapers the walls (degrees); ``thin`` makes a wall of that thickness;
        ``until``/``target`` extrude up to a boundary (``"last"`` = through everything,
        ``"next"`` = to the next face, or a resolved ``target`` face/solid).
        """

    @abstractmethod
    def revolve(self, face: Any, axis_point: Point3, axis_dir: Point3, *,
                angle: float = 360.0, symmetric: bool = False,
                thin: float | None = None) -> Any:
        """Revolve ``face`` about the axis through ``axis_point`` along ``axis_dir``.

        ``angle`` is the revolution arc in degrees (360 = full solid); ``symmetric``
        centers that arc on the profile plane; ``thin`` makes a wall of that thickness.
        Raises KernelOpError on failure (e.g. the profile crosses its axis).
        """

    @abstractmethod
    def sweep(self, profile: Any, path: Any, *, sections: list | None = None,
              guides: list | None = None, is_frenet: bool = False,
              transition: str = "transformed") -> Any:
        """Sweep ``profile`` (or ``sections``) along ``path`` into a solid.

        ``sections`` (>= 2) sweeps a variable section; ``guides`` constrain the sweep;
        ``is_frenet`` follows the path curvature (else keep-orientation); ``transition``
        is the corner style (``transformed``/``round``/``right``). Raises KernelOpError on
        failure (e.g. a self-intersecting path).
        """

    @abstractmethod
    def helix_path(self, pitch: float, height: float, radius: float, *,
                   axis_point: Point3, axis_dir: Point3, lefthand: bool = False,
                   cone_angle: float = 0.0) -> Any:
        """A helical path (a wire) for a coil/spring sweep."""

    @abstractmethod
    def circle_face(self, center: Point2, diameter: float, plane: str,
                    offset: float = 0.0) -> Any:
        """A circular planar face of ``diameter`` centred at ``center`` on ``plane``.

        ``offset`` shifts the plane along its normal by that signed distance (default 0.0).
        """

    @abstractmethod
    def wire_face(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        """A planar face from an ordered list of edge descriptors on ``plane``.

        Each edge is ``{"kind":"line","points":[a,b]}``,
        ``{"kind":"arc","points":[start,mid,end]}`` (a 3-point arc), or
        ``{"kind":"circle","center":c,"radius":r}`` (a full closed circle, its own loop).
        ``offset`` shifts the plane along its normal by that signed distance (default 0.0).
        Used by constrained sketches whose profiles mix straight and curved edges.
        """

    @abstractmethod
    def wire(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        """An OPEN wire (a path) from ordered edge descriptors on ``plane``.

        Same descriptor shape as ``wire_face`` but not closed into a face; used as a sweep
        path (an open sketch, ``open = true``). ``offset`` shifts the plane along its normal
        by that signed distance (default 0.0).
        """

    @abstractmethod
    def project_edges(self, edges: list, plane: str, offset: float = 0.0) -> list:
        """Project ``edges`` (kernel edge handles) onto ``plane``, returning 2D descriptors.

        Each descriptor is ``{"kind":"line","points":[a,b]}``,
        ``{"kind":"arc","points":[start,mid,end]}``,
        ``{"kind":"circle","center":c,"radius":r}``, or ``{"kind":"degenerate"}`` for an
        edge that projects to zero length. Coordinates are in the plane's 2D (u, v) frame.
        ``offset`` shifts the plane along its normal by that signed distance (default 0.0).
        """

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
