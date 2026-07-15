"""Abstract geometry-kernel contract.

The Builder talks only to this interface, never to a concrete backend, so the kernel
is swappable (build123d today, something else later) and Builder logic is testable
against a lightweight fake without importing a heavy CAD backend. Shapes are opaque
handles whose concrete type is the backend's business.

Coordinates and distances are in the document's canonical internal unit (millimetres).
"""

from abc import ABC, abstractmethod
from typing import Any

from ncad.kernel.element_history import ElementHistory

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
    def make_primitive(self, kind: str, dims: dict, plane: str, at: Point2) -> Any:
        """A primitive base solid: ``kind`` in {box, cylinder, sphere, cone, torus, wedge}.

        ``dims`` carries resolved numeric dimensions (box: w/d/h; cylinder: radius/h; sphere:
        radius; cone: bottom_radius/top_radius/h; torus: major_radius/minor_radius; wedge:
        dx/dy/dz). ``plane`` is the base plane ("XY"/"XZ"/"YZ") and ``at`` the 2D origin offset on
        it. A no-sketch base body (a part may start from a primitive).
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
             end_point: Point3 | None = None, guides: list | None = None,
             closed: bool = False) -> Any:
        """Blend a solid through the ordered ``sections`` (faces on different planes).

        ``ruled`` blends with straight (ruled) transitions instead of a smooth surface.
        ``start_point`` / ``end_point`` cap the ends with a vertex (a cone-like point
        section) at that ``(x, y, z)``. ``guides`` are rail curves that steer the blend (a
        guided loft). ``closed`` (periodic loft) is not supported and raises. Needs at least 2
        total sections (counting caps). Raises KernelOpError on failure.
        """

    @abstractmethod
    def rib(self, wire: Any, *, thickness: float, depth: float | None = None,
            to: Any = None, side: str = "both", draft: float = 0.0) -> Any:
        """A thin structural blade from an OPEN sketch ``wire``.

        The wire is thickened by ``thickness`` (symmetric about its curve, or ``side="one"``)
        into a thin planar profile, then grown into a blade: by ``depth`` normal to the sketch
        plane, or ``to`` a target solid (an until-material rib, auto-trimmed to the material it
        braces). ``draft`` tapers the blade walls. The caller fuses the blade into the target
        body. Raises KernelOpError on failure.
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
    def datum_plane(self, method: str, params: dict, refs: dict) -> Any:
        """A referenceable construction Plane built by ``method``.

        ``offset`` (a base plane or `refs["base"]` planar face + ``distance``), ``angled`` (a
        base plane rotated by ``angle``), ``on_face`` (`refs["face"]`), or ``three_point``
        (``params["points"]``). Non-solid reference geometry named via ``datums.<id>``.
        """

    @abstractmethod
    def datum_axis(self, method: str, params: dict, refs: dict) -> Any:
        """A referenceable axis as an ``((ox,oy,oz), (dx,dy,dz))`` tuple (revolve's axis shape).

        ``two_point`` (``params["points"]``), ``edge`` (`refs["edge"]`), ``intersection`` (of
        two datum planes in `refs`), or ``normal_to_face`` (`refs["face"]` at a point).
        """

    @abstractmethod
    def text_face(self, text: str, size: float, plane: str, *, font: str = "",
                  style: str = "", offset: float = 0.0, at: Point2 = (0.0, 0.0),
                  rotation: float = 0.0) -> Any:
        """A planar face (with glyph-counter holes) for ``text`` at ``size`` on ``plane``.

        The glyphs are built as a set of faces whose letter counters ("A", "o") are real
        inner-loop holes (multi-loop faces), placed at ``at`` (u, v) on the plane and rotated
        ``rotation`` degrees; ``offset`` shifts the plane along its normal. Extrudable/cuttable
        like any sketch profile (distinct from the ``wrap`` op, which lands text on a face).
        """

    @abstractmethod
    def fill_points(self, face: Any, spacing: float, stagger: bool = False) -> list:
        """Interior grid points over a planar ``face`` at ``spacing`` (clipped to the face).

        ``stagger`` offsets alternate rows by half a step (a hex/staggered fill). Returns
        ``[(x, y, z), ...]``. Used by the fill pattern.
        """

    @abstractmethod
    def sample_curve(self, curve: Any, count: int) -> list:
        """Uniformly sample ``curve`` at ``count`` points -> ``[(point, unit_tangent), ...]``.

        ``curve`` is a kernel Wire/Edge handle or a datum axis ``(point, dir)`` tuple. Used by
        the curve/path pattern to place instances along a rail. count 1 samples the start.
        """

    @abstractmethod
    def wire(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        """An OPEN wire (a path) from ordered edge descriptors on ``plane``.

        Same descriptor shape as ``wire_face`` but not closed into a face; used as a sweep
        path (an open sketch, ``open = true``). ``offset`` shifts the plane along its normal
        by that signed distance (default 0.0).
        """

    @abstractmethod
    def vertices_of(self, shape: Any) -> list:
        """The vertex handles of ``shape`` (a face/edge/solid). Corners for projection."""

    @abstractmethod
    def project_vertices(self, vertices: list, plane: str, offset: float = 0.0) -> list:
        """Project ``vertices`` (kernel vertex handles) onto ``plane``, returning 2D points.

        Each result is a ``(u, v)`` tuple in the sketch plane's local coords. Used to bring a
        prior feature's vertex into a sketch as a fixed construction reference point.
        """

    @abstractmethod
    def intersection_curve(self, shape: Any, plane: str, offset: float = 0.0) -> list:
        """Intersect ``shape`` with ``plane``, returning 2D sketch-edge descriptors.

        The section of the solid/face by the sketch plane, each edge projected to a
        ``wire_face``-shaped 2D descriptor. Curved section edges are refused (shared with the
        spline-projection deferral). Used to reference an intersection curve as construction
        geometry in a sketch.
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
        """Round the given ``edges`` of ``solid`` with a constant ``radius``."""

    @abstractmethod
    def fillet_variable(self, solid: Any, edges: list, radius_start: float,
                        radius_end: float) -> Any:
        """Round ``edges`` with a radius that ramps ``radius_start`` >> ``radius_end`` along
        each edge (a variable-radius fillet)."""

    @abstractmethod
    def fillet_face(self, solid: Any, faces: list, radius: float) -> Any:
        """Round every edge bounding the referenced ``faces`` with ``radius`` (a face fillet).

        Note: a true two-face-set face fillet (rolling a ball tangent to two non-adjacent face
        sets) is not native to OCCT; this rounds the faces' bounding edges.
        """

    @abstractmethod
    def chamfer_vertices(self, solid: Any, vertices: list, distance: float) -> Any:
        """Facet a corner ``vertex`` by bevelling the edges meeting it (a vertex chamfer)."""

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
    def draft_variable(self, solid: Any, face_angles: list, *, neutral: str,
                       neutral_offset: float = 0.0) -> Any:
        """Taper each planar face by its OWN angle about one neutral plane (a variable draft).

        ``face_angles`` is a list of ``(face, angle_degrees)`` pairs. Raises KernelOpError on
        failure. (Parting-line / step draft is not supported; it needs a parting-curve model.)
        """

    @abstractmethod
    def thread_cut(self, solid: Any, *, axis_point: Point3, axis_dir: Point3,
                   major_d: float, pitch: float, length: float, internal: bool) -> Any:
        """Cut (or add) a modeled helical thread on ``solid`` about the given axis.

        A triangular thread profile swept along a helix (``pitch``, ``length``, crest
        ``major_d``) straddles the crest radius; ``internal=False`` cuts an EXTERNAL thread
        (a stud), ``internal=True`` adds relief for an internal thread (a tapped hole).
        Raises KernelOpError on failure or non-positive pitch.
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
        "max_z"}`` plus, for cylindrical faces, ``axis_location``/``axis_direction``/``radius``.
        Edge dict: ``{"kind":"edge","handle","geom_type","length","center",
        "orientation","min_z","mid_z","max_z"}``.
        """

    @abstractmethod
    def axis_of(self, face: Any) -> dict | None:
        """The axis of a cylindrical ``face`` as {location, direction, radius}, or None.

        Used by coaxial/tangent relational edits to align a body to a round feature.
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
    def oriented_bounding_box(self, solid: Any) -> dict:
        """The minimum (oriented) bounding box of ``solid``.

        Returns ``{"size": (dx, dy, dz), "center": (x, y, z), "axes": [x_dir, y_dir, z_dir]}``
        where ``size[i]`` is the extent along unit direction ``axes[i]`` (dimensions plus
        orientation, as NX/Creo report a min bounding box). Unlike ``bounding_box`` (axis-aligned),
        this is the tightest box at any orientation; it is the CAM stock/blank primitive.
        """

    @abstractmethod
    def place(self, shape: Any, matrix: list[list[float]]) -> Any:
        """Return ``shape`` placed by a row-major 4x4 rigid matrix (rotation top-left, translation
        in the last row): the assembly placement convention, to world-place an instance solid."""

    @abstractmethod
    def distance(self, shape_a: Any, shape_b: Any) -> float:
        """Minimum distance between two solids (0.0 if touching or overlapping)."""

    @abstractmethod
    def closest_points(self, shape_a: Any, shape_b: Any) -> tuple[Point3, Point3]:
        """The nearest point pair ``(point_on_a, point_on_b)`` between two shapes (world coords).

        The point-level companion to ``distance`` (the scalar gap); the pair coincides when the
        shapes touch or overlap.
        """

    @abstractmethod
    def common_volume(self, shape_a: Any, shape_b: Any) -> float:
        """Volume of the boolean intersection of two solids (0.0 if disjoint or merely touching)."""

    @abstractmethod
    def bodies(self, shape: Any) -> list:
        """The bodies of ``shape`` as a list of ``Body``.

        A plain single shape returns a one-element list (a default-id solid body); a
        ``BodySet`` returns its bodies. Lets callers iterate a part's bodies uniformly.
        """

    @abstractmethod
    def mesh_body_ids(self, shape: Any) -> list:
        """The body id of each exported glTF mesh, in export (mesh) order.

        The glTF export flattens each body to its solid(s), one mesh per solid, in body order.
        This returns the parallel list of body ids so the viewer can map mesh index -> body ->
        material without relying on glTF names surviving the loader. A single shape yields one
        entry (its implicit body id).
        """

    @abstractmethod
    def union_bodies(self, shapes: list, *, origin: str, sources: list | None = None) -> Any:
        """Collect ``shapes`` as separate bodies in one BodySet (a keep-separate union).

        A plain shape becomes a new body with id ``<origin>/body/<n>`` (minted at birth); a
        shape that is already a BodySet keeps its bodies' existing ids (a body is born once,
        not re-minted per feature). Used by ``boolean merge=false``. ``sources`` (optional,
        aligned with ``shapes``) sets each plain-shape body's ``created_by`` to its source
        feature id, so per-body provenance/material survives assembly (None falls back to
        ``origin``).
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
    def mirror(self, shape: Any, *, plane: dict) -> Any:
        """Return ``shape`` reflected across ``plane`` (orientation-corrected).

        ``plane`` is a normalized description: ``{"kind":"base","plane":"XY"/"XZ"/"YZ",
        "offset": float}`` (a base plane shifted along its normal) or ``{"kind":"custom",
        "point": (x,y,z), "z_dir": (x,y,z)}`` (an arbitrary plane through ``point`` with
        normal ``z_dir``). A reflection is a negative-determinant transform, so the backend
        must correct face orientation (return a valid solid). A ``BodySet`` is reflected per
        body, ids preserved. Raises KernelOpError on failure.
        """

    @abstractmethod
    def split(self, shape: Any, *, plane: dict, keep: str) -> list:
        """Split ``shape`` by ``plane``; return the kept side(s) as raw shapes.

        ``plane`` is the normalized description (see mirror). ``keep`` is ``"both"`` (return
        ``[top, bottom]`` - the positive then the negative side of the plane normal),
        ``"top"`` (return ``[top]``), or ``"bottom"`` (return ``[bottom]``). The op wraps a
        2-shape result into an addressable BodySet. Raises KernelOpError on failure.
        """

    @abstractmethod
    def inertia(self, solid: Any) -> dict:
        """The volume inertia of ``solid`` -> ``{"matrix": 3x3, "principal": [i1,i2,i3],
        "gyradius": [gx,gy,gz]}``.

        Density-1 (geometry-only, like volume); the mass layer scales by material density.
        ``gyradius`` is the radius of gyration about the world X, Y, Z axes.
        """

    @abstractmethod
    def split_by_tool(self, shape: Any, tool: Any, keep: str = "both") -> list:
        """Partition ``shape`` by a TOOL BODY: the region inside the tool + the region outside.

        ``keep`` is ``"both"`` (return ``[inside, outside]``), ``"inside"``, or ``"outside"``.
        Each region may be a Compound of several solids. Raises KernelOpError on failure.
        """

    @abstractmethod
    def defeature(self, solid: Any, face: Any) -> Any:
        """Remove ``face`` from ``solid`` (BRepAlgoAPI_Defeaturing); raise on OCCT failure."""

    @abstractmethod
    def offset_solid(self, solid: Any, distance: float) -> Any:
        """Offset the whole ``solid`` by ``distance`` (outward > 0); raise on OCCT failure."""

    @abstractmethod
    def move_face(self, solid: Any, face: Any, distance: float) -> Any:
        """Push planar ``face`` of ``solid`` along its normal by ``distance``.

        Outward (> 0) fuses a slab; inward (< 0) cuts one. OCCT has no native move-face, so this
        is synthesized (extrude-slab + boolean + heal) and must be guarded + oracle-verified.
        Raises on OCCT failure.
        """

    @abstractmethod
    def face_neighbours(self, solid: Any, face: Any) -> list[Any]:
        """The faces of ``solid`` that share an edge with ``face``."""

    @abstractmethod
    def is_tangent_adjacent(self, solid: Any, face: Any) -> bool:
        """True if ``face`` meets any neighbour with tangent (G1) continuity.

        Used by the direct-edit guard: defeature silently no-ops on tangent-adjacent faces
        (4.0 envelope), so such a target is refused.
        """

    @abstractmethod
    def min_wall_thickness(self, solid: Any) -> float | None:
        """An estimate of ``solid``'s smallest wall thickness, or None if not computable.

        The guard fails safe (refuses an inward offset) when this is None.
        """

    @abstractmethod
    def import_solid(self, path: str) -> Any:
        """Read a solid B-rep from ``path`` (STEP/IGES); the base of an imported document."""

    @abstractmethod
    def history(self, inputs: list[Any], output: Any) -> ElementHistory:
        """Report the lineage of ``output`` relative to ``inputs`` (design section 2).

        Returns an ElementHistory mapping output sub-shape handles to the input handles they
        were generated from / modified from, plus the inputs that were deleted. Output handles
        in neither map are carried unchanged. Backends without usable history for an op may
        return an empty ElementHistory; the naming layer then falls back to geometric seed
        names for that op's output.
        """

    @abstractmethod
    def export(self, solid: Any, path: str, body_colors: dict | None = None) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension.

        ``body_colors`` (optional) maps a body id to an ``(r, g, b, a)`` color in 0..1; a glTF
        export writes it as the per-body PBR baseColorFactor so authored appearance colors port
        to other renderers. Ignored for STEP/STL.
        """

    @abstractmethod
    def export_assembly(self, components: list[dict], path: str) -> None:
        """Write a structured STEP AP242 assembly: named, colored part labels + placed components.

        Each component is ``{shape, name, color, material, placement}`` where placement is a
        row-major 4x4 (mm). Distinct part names become distinct part labels; instances become
        located components under a root assembly label.
        """
