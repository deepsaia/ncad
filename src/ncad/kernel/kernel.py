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
    def loft(self, sections: list, *, ruled: bool = False,
             start_point: Point3 | None = None,
             end_point: Point3 | None = None) -> Any:
        """Blend a solid through the ordered ``sections`` (faces on different planes).

        ``ruled`` blends with straight (ruled) transitions instead of a smooth surface.
        ``start_point`` / ``end_point`` cap the ends with a vertex (a cone-like point
        section) at that ``(x, y, z)``. Needs at least 2 total sections (counting caps).
        Raises KernelOpError on failure.
        """

    @abstractmethod
    def rib(self, wire: Any, *, thickness: float, depth: float) -> Any:
        """A thin structural blade from an OPEN sketch ``wire``.

        The wire is thickened by ``thickness`` symmetrically about its curve into a thin
        planar profile, then grown ``depth`` normal to the sketch plane into a blade solid.
        The caller fuses the blade into the target body. Raises KernelOpError on failure.
        """

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
    def cone(self, center: Point3, axis: str, bottom_diameter: float,
             top_diameter: float, length: float) -> Any:
        """A (possibly truncated) cone from ``center`` along ``axis``.

        ``bottom_diameter`` at the base (``center``), ``top_diameter`` at ``length`` along
        ``axis`` (0 = a pointed tip). Used as the countersink frustum tool.
        """

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
    def chamfer_edges(self, solid: Any, edges: list, distance: float, *,
                      distance2: float | None = None,
                      angle: float | None = None) -> Any:
        """Bevel ``edges`` of ``solid`` by ``distance``.

        ``distance2`` (a second setback) makes a two-distance chamfer; ``angle`` (degrees)
        makes a distance-angle chamfer measured from an auto-picked adjacent face. At most
        one of ``distance2``/``angle`` may be given; both None is a symmetric chamfer.
        Raises KernelOpError on failure.
        """

    @abstractmethod
    def shell(self, solid: Any, thickness: float, openings: list | None = None) -> Any:
        """Hollow ``solid`` to a wall of ``thickness`` (inward).

        ``openings`` is a list of face handles to remove (an open shell); None keeps a
        closed shell. Raises KernelOpError on failure.
        """

    @abstractmethod
    def draft(self, solid: Any, faces: list, *, angle: float, neutral: str,
              neutral_offset: float = 0.0) -> Any:
        """Taper ``faces`` of ``solid`` by ``angle`` degrees about a neutral plane.

        ``neutral`` is one of ``"XY"``, ``"XZ"``, ``"YZ"``; ``neutral_offset`` shifts that
        plane along its normal (the sketch plane_offset convention). The neutral
        cross-section keeps its size while the faces taper. Raises KernelOpError on failure.
        """

    @abstractmethod
    def wrap(self, solid: Any, face: Any, *, text: str | None = None,
             profile: Any = None, font_size: float = 5.0, font: str = "Arial",
             font_style: str = "regular", depth: float = 1.0, mode: str = "emboss",
             offset: Point2 = (0.0, 0.0), rotation: float = 0.0) -> Any:
        """Emboss or engrave a 2D profile onto a flat ``face`` of ``solid``.

        Exactly one of ``text`` (built as glyphs at ``font_size``/``font``/``font_style``)
        or ``profile`` (a face handle) is the shape. It is placed on ``face``'s plane,
        shifted by ``offset`` (u, v) and rotated ``rotation`` degrees, then extruded
        ``depth`` and added (``mode="emboss"``) or cut (``mode="engrave"``). Raises
        KernelOpError on failure.
        """

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
    def bodies(self, shape: Any) -> list:
        """The bodies of ``shape`` as a list of ``Body``.

        A plain single shape returns a one-element list (a default-id solid body); a
        ``BodySet`` returns its bodies. Lets callers iterate a part's bodies uniformly.
        """

    @abstractmethod
    def union_bodies(self, shapes: list, *, origin: str) -> Any:
        """Collect ``shapes`` as separate bodies in one BodySet (a keep-separate union).

        A plain shape becomes a new body with id ``<origin>/body/<n>`` (minted at birth); a
        shape that is already a BodySet keeps its bodies' existing ids (a body is born once,
        not re-minted per feature). Used by ``boolean merge=false``.
        """

    @abstractmethod
    def transform(self, shape: Any, *, move: Point3 = (0.0, 0.0, 0.0),
                  rotate: dict | None = None, scale: Any = None) -> Any:
        """Return ``shape`` transformed by scale >> rotate >> move (in that order).

        ``move`` is a translation ``(dx,dy,dz)``. ``rotate`` is ``{"axis": (x,y,z),
        "angle": degrees, "about": (x,y,z)}`` or None. ``scale`` is a float (uniform) or a
        ``(sx,sy,sz)`` tuple (non-uniform), or None. Rigid transforms are exact; non-uniform
        scale is validity-gated. Raises KernelOpError on failure.
        """

    @abstractmethod
    def export(self, solid: Any, path: str) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension."""
