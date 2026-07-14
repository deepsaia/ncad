"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and exports to glTF / STEP /
STL. Importing this module pulls in OCP, which is slow on first load; keep it out of
the fast test path.
"""

import importlib.metadata
import logging
import math
from typing import Any

from build123d import (
    Axis,
    CenterOf,
    Edge,
    Face,
    FontStyle,
    GeomType,
    Helix,
    Keep,
    Location,
    Plane,
    Pos,
    Rot,
    Solid,
    Text,
    Transition,
    Unit,
    Until,
    Vector,
    Vertex,
    Wire,
    available_fonts,
    draft,
    export_gltf,
    export_step,
    export_stl,
    extrude,
    loft,
    offset,
    revolve,
    sweep,
    trace,
)

# OCP ships incomplete stubs, so these raw-OCP names read as missing to the type checker;
# they resolve at runtime (see the [tool.pyrefly] OCP-boundary note). Used for the per-edge
# distance-angle chamfer that build123d cannot express.
from OCP.BRep import BRep_Tool  # pyrefly: ignore[missing-module-attribute]
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Defeaturing,  # pyrefly: ignore[missing-module-attribute]
    BRepAlgoAPI_Section,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_GTransform,  # pyrefly: ignore[missing-module-attribute]
    BRepBuilderAPI_MakeEdge,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # pyrefly: ignore[missing-module-attribute]
from OCP.BRepFilletAPI import (
    BRepFilletAPI_MakeChamfer,  # pyrefly: ignore[missing-module-attribute]
    BRepFilletAPI_MakeFillet,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.BRepOffsetAPI import (
    BRepOffsetAPI_DraftAngle,  # pyrefly: ignore[missing-module-attribute]
    BRepOffsetAPI_MakePipeShell,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.Geom import Geom_BezierCurve  # pyrefly: ignore[missing-module-attribute]
from OCP.GeomAbs import GeomAbs_G1  # pyrefly: ignore[missing-module-attribute]
from OCP.gp import (
    gp_Dir,  # pyrefly: ignore[missing-module-attribute]
    gp_GTrsf,  # pyrefly: ignore[missing-module-attribute]
    gp_Pln,  # pyrefly: ignore[missing-module-attribute]
    gp_Pnt,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.TColgp import TColgp_Array1OfPnt  # pyrefly: ignore[missing-module-attribute]
from OCP.TColStd import TColStd_Array1OfReal  # pyrefly: ignore[missing-module-attribute]
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE  # pyrefly: ignore[missing-module-attribute]
from OCP.TopExp import TopExp, TopExp_Explorer  # pyrefly: ignore[missing-module-attribute]
from OCP.TopoDS import TopoDS  # pyrefly: ignore[missing-module-attribute]
from OCP.TopTools import (
    TopTools_IndexedDataMapOfShapeListOfShape,  # pyrefly: ignore[missing-module-attribute]
    TopTools_ListOfShape,  # pyrefly: ignore[missing-module-attribute]
)

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet, union_bodies
from ncad.kernel.element_history import ElementHistory
from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3
from ncad.kernel.kernel_op_error import KernelOpError

logger = logging.getLogger(__name__)

_PLANES = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}
_KEEP = {"top": Keep.TOP, "bottom": Keep.BOTTOM}
_AXES = {"X": Axis.X, "Y": Axis.Y, "Z": Axis.Z}
_FONT_STYLES = {"regular": FontStyle.REGULAR, "bold": FontStyle.BOLD,
                "italic": FontStyle.ITALIC}
# End-condition until-token -> build123d Until. "last" = through everything.
_UNTIL_TOKENS = {"last": Until.LAST, "next": Until.NEXT}
_TRANSITIONS = {"transformed": Transition.TRANSFORMED, "round": Transition.ROUND,
                "right": Transition.RIGHT}
# glTF tessellation angular deflection (radians): the cross-section smoothness lever.
# build123d's default 0.1 over-refines a curvature-heavy helix; 0.2 (~11 degrees, a ~32-gon
# tube) stays visibly smooth while fast. Higher values (0.5) visibly facet a thin swept
# tube. Paired with a bbox-relative linear deflection (_deflection); together they are the
# pinned viewer tessellation.
_ANGULAR_DEFLECTION = 0.2


_DEFAULT_FONT = "Arial"


def _resolve_font(font: str) -> str:
    """Return ``font`` if installed, else the default (logged).

    build123d/OCCT silently falls back to a default font (Arial) with only a stderr warning
    when a requested font is missing; this makes the fallback explicit and logs it through our
    logger so a missing font on the ncad host is visible, and returns a font name that builds.
    """
    if not font:
        return _DEFAULT_FONT
    try:
        installed = {info.name for info in available_fonts()}
    except Exception:  # noqa: BLE001 - font enumeration is best-effort; fall through to trust
        return font
    if font in installed:
        return font
    logger.warning("font %r is not installed on this host; falling back to %r",
                   font, _DEFAULT_FONT)
    return _DEFAULT_FONT


def _wrap_curved(solid: Any, face: Any, shape2d: Any, offset: Point2, rotation: float,
                 depth: float, mode: str) -> Any:
    """Emboss/engrave a 2D profile onto a curved (cylinder/cone) face by projecting it.

    The flat glyph/profile faces are placed tangent to the curved wall at the target point,
    projected onto the surface (build123d Face.project_to_shape), then thickened along each
    projected face's normal (outward = emboss, inward = engrave).
    """
    center = face.center()
    normal = face.normal_at(center)
    # A tangent placement plane at the face center: its Z is the outward surface normal, so
    # the flat text sits just off the wall facing inward for projection.
    place = Plane(origin=center + normal * depth, z_dir=-normal)
    flat = place * Pos(offset[0], offset[1]) * Rot(0, 0, rotation) * shape2d  # pyrefly: ignore[unsupported-operation]
    direction = (-normal.X, -normal.Y, -normal.Z)
    result = solid
    for glyph in flat.faces():
        for projected in glyph.project_to_shape(solid, direction=direction):
            # project_to_shape may hand back a Shell; thicken each of its faces along the
            # surface normal. emboss grows OUTWARD (+normal) and adds; engrave grows INWARD
            # (-normal) and cuts, so the tool lands inside the wall.
            for pf in projected.faces():
                pnormal = pf.normal_at(pf.center())
                grow = pnormal if mode == "emboss" else -pnormal
                tool = extrude(pf, amount=abs(depth), dir=grow)  # pyrefly: ignore[bad-argument-type]
                result = result + tool if mode == "emboss" else result - tool
    return result


def _axis_to_wire(axis: Any) -> Any:
    """A finite Wire from a datum axis ``((ox,oy,oz), (dx,dy,dz))`` (unit length 1 by dir).

    A datum axis is infinite; sampling needs a finite span, so build a unit-length segment
    from the axis point along its direction. The caller controls extent by the number of
    samples * the pattern spacing, not by this segment's length.
    """
    (ox, oy, oz), (dx, dy, dz) = axis
    start = Vector(ox, oy, oz)
    end = Vector(ox + dx, oy + dy, oz + dz)
    return Wire([Edge.make_line(start, end)])  # pyrefly: ignore[bad-argument-type]


def _basis(plane: Any, offset: float) -> Any:
    """The build123d Plane to sketch on: a base-plane string (+ offset), or a datum Plane.

    A datum plane (from a `datum_plane` feature, resolved via `datums.<id>`) arrives as a
    build123d Plane and is used directly (its own offset already baked in); a base-plane
    string is looked up and shifted along its normal by ``offset``.
    """
    if isinstance(plane, str):
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        return _PLANES[plane].offset(offset)
    return plane if offset == 0.0 else plane.offset(offset)


class Build123dKernel(Kernel):
    """build123d-backed kernel. Shapes are build123d ``Face``/``Solid`` objects."""

    def polygon_face(self, points: list[Point2], plane: Any, offset: float = 0.0) -> Any:
        # offset shifts the base plane along its normal; default 0.0 keeps prior behavior. A
        # datum plane (resolved from datums.<id>) may arrive as a build123d Plane.
        basis = _basis(plane, offset)
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

    def extrude(self, face: Any, distance: float | None = None, *,
                symmetric: bool = False, second_distance: float | None = None,
                draft: float = 0.0, thin: float | None = None,
                until: str | None = None, target: Any = None) -> Any:
        to_extrude = _thin_ring(face, thin) if thin is not None else face
        if until is not None or target is not None:
            until_token = _UNTIL_TOKENS.get(until) if until is not None else None
            return extrude(to_extrude, until=until_token, target=target, taper=draft)
        if distance is None:
            raise KernelOpError("extrude needs a distance unless an until/target is given")
        amount = float(distance)
        if second_distance is not None:
            forward = extrude(to_extrude, amount=amount, taper=draft)
            back = extrude(to_extrude, amount=-float(second_distance), taper=draft)
            return self.fuse([forward, back])
        if symmetric:
            # build123d both=True extrudes `amount` in EACH direction (verified: it doubles
            # the height). Halve so the TOTAL symmetric height equals `distance`, matching
            # the FakeKernel model and the blind-vs-symmetric equal-volume test.
            return extrude(to_extrude, amount=amount / 2.0, both=True, taper=draft)
        return extrude(to_extrude, amount=amount, taper=draft)

    def revolve(self, face: Any, axis_point: Point3, axis_dir: Point3, *,
                angle: float = 360.0, symmetric: bool = False,
                thin: float | None = None) -> Any:
        profile = _thin_ring(face, thin) if thin is not None else face
        axis = Axis(tuple(axis_point), tuple(axis_dir))  # pyrefly: ignore[no-matching-overload]
        if symmetric and angle < 360.0:
            # Center the arc on the profile plane by rotating the profile back by half the
            # angle, then sweeping the full angle forward: the swept volume is identical to
            # a plain partial revolve, just centered (verified by the equal-volume test).
            profile = profile.rotate(axis, -angle / 2.0)
        return revolve(profile, axis, revolution_arc=angle)

    def sweep(self, profile: Any, path: Any, *, sections: list | None = None,
              guides: list | None = None, is_frenet: bool = False,
              transition: str = "transformed") -> Any:
        # multisection sweeps the given section faces along the path (build123d places them
        # by order); a single profile sweeps as a constant section. guides are accepted but
        # build123d's binormal/guide support is narrow, so they are not passed in this
        # bucket (the plan records guide curves as approximating a plain sweep).
        to_sweep = sections if sections else profile
        return sweep(to_sweep, path=path, multisection=sections is not None,
                     is_frenet=is_frenet, transition=_TRANSITIONS[transition])

    def helix_path(self, pitch: float, height: float, radius: float, *,
                   axis_point: Point3, axis_dir: Point3, lefthand: bool = False,
                   cone_angle: float = 0.0) -> Any:
        return Helix(pitch, height, radius, center=tuple(axis_point),
                     direction=tuple(axis_dir), lefthand=lefthand,
                     cone_angle=cone_angle)  # pyrefly: ignore[no-matching-overload]

    def loft(self, sections: list, *, ruled: bool = False,
             start_point: Point3 | None = None,
             end_point: Point3 | None = None, guides: list | None = None,
             closed: bool = False) -> Any:
        # Closed/periodic loft (sections looping back to the first) is NOT supported: OCCT
        # ThruSections does not build a valid periodic solid (a closed section loop yields
        # zero volume). Called out rather than silently producing an empty solid.
        if closed:
            raise KernelOpError(
                "closed/periodic loft is not supported (OCCT ThruSections has no periodic "
                "mode); loft open sections, or model the closed form another way")
        if guides:
            # Guided loft: sweep the first section along an implicit spine while a guide rail
            # steers the section (build123d's loft has no guide support; use OCCT
            # MakePipeShell with the guide in binormal mode). This is the NX/Creo/Fusion
            # rail-guided loft.
            return self._robust(self._do_guided_loft, sections, guides, name="loft")
        # A vertex cap is a zero-area point section: build123d loft accepts Vertex in the
        # section list, giving a cone-like end. Order matters: caps bracket the faces.
        ordered: list = []
        if start_point is not None:
            ordered.append(Vertex(*start_point))
        ordered.extend(sections)
        if end_point is not None:
            ordered.append(Vertex(*end_point))
        return loft(ordered, ruled=ruled)

    @staticmethod
    def _do_guided_loft(sections: list, guides: list) -> Any:
        from build123d import Solid
        # A spine from the first section's center to the last; each section added as a
        # profile; the first guide steers the sweep (binormal mode).
        first_center = sections[0].center()
        last_center = sections[-1].center()
        spine = Wire(Edge.make_line(first_center, last_center))
        maker = BRepOffsetAPI_MakePipeShell(spine.wrapped)
        maker.SetMode(guides[0].wrapped, True)
        for section in sections:
            outer = section.outer_wire() if hasattr(section, "outer_wire") else section
            maker.Add(outer.wrapped, False, False)
        maker.Build()
        maker.MakeSolid()
        return Solid(maker.Shape())

    def rib(self, wire: Any, *, thickness: float, depth: float | None = None,
            to: Any = None, side: str = "both", draft: float = 0.0) -> Any:
        # Planar-first (robust): thicken the open wire IN ITS OWN PLANE with trace into a
        # closed ribbon face, then extrude that face. This avoids OCCT's fragile
        # offset/thicken-a-shell path (design.md: BRepOffsetAPI_MakeOffsetShape fails on C0
        # splines and past the smallest concave radius). thickness is symmetric about the
        # curve by default; side="one" thickens to one side (a rib flush with the sketch).
        line_width = thickness if side == "both" else thickness
        ribbon = trace(wire, line_width=line_width)
        # A ribbon traced around a curved wire is planar but build123d cannot infer the
        # extrude direction from it, so pass the ribbon face's normal explicitly.
        normal = ribbon.faces()[0].normal_at()  # pyrefly: ignore[bad-argument-type]
        if to is not None:
            # Until-material: grow the blade until it meets `to` (auto-trimmed), so a gusset
            # needs no manual boolean-trim. This is the NX/Creo until-next rib extent.
            return self._robust(self._do_rib_until, ribbon, to, name="rib")
        if depth is None:
            raise KernelOpError("rib needs a 'depth' unless an until-material 'to' is given")
        return extrude(ribbon, amount=depth, dir=normal, taper=draft)

    @staticmethod
    def _do_rib_until(ribbon: Any, target: Any) -> Any:
        # Try both normal directions (a rib blade grows toward the material it braces); pick
        # whichever until-material extrude yields a non-empty solid.
        for token in (Until.NEXT, Until.LAST):
            grown = extrude(ribbon, until=token, target=target)
            if grown is not None and grown.volume > 1e-9:
                return grown
        raise KernelOpError("until-material rib grew no material toward the target")

    def circle_face(self, center: Point2, diameter: float, plane: Any,
                    offset: float = 0.0) -> Any:
        basis = _basis(plane, offset)
        # from_local_coords is stubbed as a wide union but returns a Vector at runtime;
        # this is the untyped-OCP boundary (see the [tool.pyrefly] note in pyproject).
        origin = basis.from_local_coords(Vector(center[0], center[1], 0))
        face_plane = Plane(origin=origin, z_dir=basis.z_dir)  # pyrefly: ignore[no-matching-overload]
        return Face(Wire(Edge.make_circle(diameter / 2.0, face_plane)))

    def wire_face(self, edges: list, plane: Any, offset: float = 0.0) -> Any:
        basis = _basis(plane, offset)
        occ_edges = [_build_edge(edge, basis) for edge in edges]
        return Face(Wire(occ_edges))

    def text_face(self, text: str, size: float, plane: Any, *, font: str = "",
                  style: str = "", offset: float = 0.0, at: Point2 = (0.0, 0.0),
                  rotation: float = 0.0) -> Any:
        basis = _basis(plane, offset)
        font_style = _FONT_STYLES.get(style, FontStyle.REGULAR)
        # build123d Text yields a Sketch of glyph faces whose letter counters are inner-loop
        # holes (multi-loop faces). A missing font falls back to the default (logged), matching
        # the wrap op. Placed on the sketch plane at (u, v) with in-plane rotation.
        kwargs: dict = {"font_size": size, "font_style": font_style}
        if font:
            kwargs["font"] = _resolve_font(font)
        glyphs = Text(text, **kwargs)
        return basis * Pos(at[0], at[1]) * Rot(0, 0, rotation) * glyphs  # pyrefly: ignore[unsupported-operation]

    def datum_plane(self, method: str, params: dict, refs: dict) -> Any:
        if method == "offset":
            face = refs.get("face")
            src = Plane(face) if face is not None else _PLANES.get(params.get("base") or "XY",
                                                                   Plane.XY)
            return src.offset(params["distance"])
        if method == "on_face":
            face = refs.get("face")
            if face is None:
                raise KernelOpError("datum_plane on_face needs a face reference")
            return Plane(face)
        if method == "angled":
            base = _PLANES.get(params.get("base") or "XY", Plane.XY)
            return base.rotated((params["angle"], 0.0, 0.0))
        if method == "three_point":
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = params["points"]
            a = Vector(ax, ay, az)
            x_dir = Vector(bx, by, bz) - a
            normal = x_dir.cross(Vector(cx, cy, cz) - a)
            return Plane(origin=a, x_dir=x_dir, z_dir=normal)  # pyrefly: ignore[no-matching-overload]
        raise KernelOpError(f"unknown datum_plane method {method!r}")

    def datum_axis(self, method: str, params: dict, refs: dict) -> Any:
        if method == "two_point":
            (ax, ay, az), (bx, by, bz) = params["points"]
            direction = Vector(bx - ax, by - ay, bz - az)
            if direction.length < 1e-9:
                raise KernelOpError("datum_axis two_point needs two distinct points")
            unit = direction.normalized()
            return ((ax, ay, az), (unit.X, unit.Y, unit.Z))
        if method == "edge":
            edge = refs.get("edge")
            edge = edge[0] if isinstance(edge, list) else edge
            if edge is None:
                raise KernelOpError("datum_axis edge needs an edge reference")
            p0 = edge.position_at(0)
            direction = (edge.position_at(1) - p0).normalized()
            return ((p0.X, p0.Y, p0.Z), (direction.X, direction.Y, direction.Z))
        if method == "normal_to_face":
            face = refs.get("face")
            if face is None:
                raise KernelOpError("datum_axis normal_to_face needs a face reference")
            at = params.get("at_point")
            origin = Vector(*at) if at is not None else face.center()
            normal = face.normal_at(origin)
            return ((origin.X, origin.Y, origin.Z), (normal.X, normal.Y, normal.Z))
        if method == "intersection":
            planes = refs.get("planes") or []
            if len(planes) != 2:
                raise KernelOpError("datum_axis intersection needs two plane references")
            direction = planes[0].z_dir.cross(planes[1].z_dir).normalized()
            origin = planes[0].origin
            return ((origin.X, origin.Y, origin.Z), (direction.X, direction.Y, direction.Z))
        raise KernelOpError(f"unknown datum_axis method {method!r}")

    def fill_points(self, face: Any, spacing: float, stagger: bool = False) -> list:
        # A grid of interior points over a planar face at `spacing`, clipped to the face by
        # is_inside (so a non-rectangular face fills correctly). stagger offsets alternate rows
        # by half a step (a hex/staggered fill). Used by the fill pattern.
        bb = face.bounding_box()
        pts: list = []
        row = 0
        y = bb.min.Y
        while y <= bb.max.Y + 1e-9:
            offset = spacing / 2.0 if (stagger and row % 2) else 0.0
            x = bb.min.X + offset
            while x <= bb.max.X + 1e-9:
                p = Vector(x, y, bb.min.Z)
                if face.is_inside(p):
                    pts.append((p.X, p.Y, p.Z))
                x += spacing
            y += spacing
            row += 1
        return pts

    def sample_curve(self, curve: Any, count: int) -> list:
        # Uniformly sample a curve (a Wire/Edge or a datum axis) at count points, returning
        # (point, unit-tangent) tuples. t in [0, 1]; count 1 samples the start. Used by the
        # curve/path pattern to place instances along a rail.
        wire = curve if hasattr(curve, "__matmul__") else _axis_to_wire(curve)
        out: list = []
        for i in range(count):
            t = 0.0 if count <= 1 else i / (count - 1)
            p = wire @ t
            d = wire % t
            out.append(((p.X, p.Y, p.Z), (d.X, d.Y, d.Z)))
        return out

    def wire(self, edges: list, plane: Any, offset: float = 0.0) -> Any:
        basis = _basis(plane, offset)
        return Wire([_build_edge(edge, basis) for edge in edges])

    def project_edges(self, edges: list, plane: Any, offset: float = 0.0) -> list:
        basis = _basis(plane, offset)
        return [_project_edge(edge, basis) for edge in edges]

    def vertices_of(self, shape: Any) -> list:
        return list(shape.vertices())

    def project_vertices(self, vertices: list, plane: Any, offset: float = 0.0) -> list:
        basis = _basis(plane, offset)
        out: list = []
        for v in vertices:
            local = basis.to_local_coords(Vector(v.X, v.Y, v.Z))
            out.append((local.X, local.Y))  # pyrefly: ignore[missing-attribute]
        return out

    def intersection_curve(self, shape: Any, plane: Any, offset: float = 0.0) -> list:
        basis = _basis(plane, offset)
        # OCCT section of the shape with the sketch plane; each resulting edge is projected to
        # a 2D sketch-plane descriptor (curved edges are refused by _project_edge, matching the
        # existing spline-projection deferral).
        section = BRepAlgoAPI_Section(_wrapped(shape), basis.wrapped)
        section.Build()
        descriptors: list = []
        explorer = TopExp_Explorer(section.Shape(), TopAbs_EDGE)
        while explorer.More():
            edge = Edge(TopoDS.Edge_s(explorer.Current()))
            descriptors.append(_project_edge(edge, basis))
            explorer.Next()
        return descriptors

    def cylinder(self, center: Point3, axis: str, diameter: float, length: float) -> Any:
        if axis not in _AXES:
            raise ValueError(f"axis must be one of {tuple(_AXES)}, got {axis!r}")
        base = Plane(origin=Vector(*center), z_dir=_AXES[axis].direction)
        return Solid.make_cylinder(diameter / 2.0, length, base)

    def cone(self, center: Point3, axis: str, bottom_diameter: float,
             top_diameter: float, length: float) -> Any:
        if axis not in _AXES:
            raise ValueError(f"axis must be one of {tuple(_AXES)}, got {axis!r}")
        # Same placement as cylinder: a base plane at center oriented along axis.
        base = Plane(origin=Vector(*center), z_dir=_AXES[axis].direction)
        return Solid.make_cone(bottom_diameter / 2.0, top_diameter / 2.0, length, base)

    def cut(self, solid: Any, tools: list) -> Any:
        return self._robust(self._do_cut, solid, tools, name="cut")

    def fuse(self, solids: list) -> Any:
        return self._robust(self._do_fuse, solids, name="fuse")

    def intersect(self, solids: list) -> Any:
        return self._robust(self._do_intersect, solids, name="intersect")

    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        return self._robust(self._do_fillet, solid, edges, radius, name="fillet")

    def fillet_variable(self, solid: Any, edges: list, radius_start: float,
                        radius_end: float) -> Any:
        return self._robust(self._do_fillet_variable, solid, edges, radius_start,
                            radius_end, name="fillet")

    def fillet_face(self, solid: Any, faces: list, radius: float) -> Any:
        # A "face fillet" here rounds every edge BOUNDING the referenced face(s). OCCT fillets
        # shared edges only; a true NX-style face fillet between two NON-adjacent face sets
        # (rolling a ball tangent to both) is not native to OCCT and is not supported (call it
        # out rather than fake it). The bounding-edges form is the common case.
        edges = [e for face in faces for e in face.edges()]
        return self._robust(self._do_fillet, solid, edges, radius, name="fillet")

    def chamfer_vertices(self, solid: Any, vertices: list, distance: float) -> Any:
        # A vertex (corner) chamfer facets the corner by bevelling the edges meeting it.
        edges = [e for v in vertices for e in self._edges_at_vertex(solid, v)]
        return self._robust(self._do_chamfer, solid, edges, distance, None, name="chamfer")

    @staticmethod
    def _edges_at_vertex(solid: Any, vertex: Any) -> list:
        """The edges of ``solid`` incident to ``vertex`` (by coincident position)."""
        target = tuple(vertex)
        incident = []
        for edge in solid.edges():
            if any(tuple(v) == target for v in edge.vertices()):
                incident.append(edge)
        return incident

    def chamfer_edges(self, solid: Any, edges: list, distance: float, *,
                      distance2: float | None = None,
                      angle: float | None = None) -> Any:
        if angle is not None:
            # build123d's distance-angle chamfer requires ALL edges to share one reference
            # face; raw OCP AddDA takes a per-edge face, so we auto-pick each edge's first
            # adjacent face and build via BRepFilletAPI_MakeChamfer. Gated by _robust.
            return self._robust(self._do_chamfer_angle, solid, edges, distance, angle,
                                name="chamfer")
        return self._robust(self._do_chamfer, solid, edges, distance, distance2,
                            name="chamfer")

    def shell(self, solid: Any, thickness: float, openings: list | None = None) -> Any:
        # build123d offset hollows inward with a negative amount; openings (a list of face
        # handles) are the faces to remove for an open shell. Gated by _robust.
        return self._robust(self._do_shell, solid, thickness, openings, name="shell")

    @staticmethod
    def _do_shell(solid: Any, thickness: float, openings: list | None) -> Any:
        return offset(solid, amount=-abs(thickness), openings=openings)

    def draft(self, solid: Any, faces: list, *, angle: float, neutral: str,
              neutral_offset: float = 0.0) -> Any:
        if neutral not in _PLANES:
            raise KernelOpError(
                f"draft neutral must be one of {tuple(_PLANES)}, got {neutral!r}")
        # The neutral plane reuses the plane_offset convention: a base plane shifted along
        # its normal. draft() keeps that cross-section fixed while the faces taper. The
        # module-level `draft` function (not the local `draft` taper param on extrude/
        # revolve) does the work.
        plane = _PLANES[neutral].offset(neutral_offset)
        # Draft is only defined for PLANAR faces (a taper angle about a neutral plane has no
        # meaning on a cylinder/sphere, and OCCT DraftAngle rejects them). A face-keyword
        # like `vertical` can select cylindrical walls (fillet rounds, boss, hole bores)
        # alongside planar ones, so filter to planar faces here rather than letting the whole
        # op fail. This matches CAD tools, which draft planar walls only.
        planar = [f for f in faces if getattr(f, "geom_type", None) == GeomType.PLANE]
        if not planar:
            raise KernelOpError("draft found no planar faces among the selected faces")
        return self._robust(self._do_draft, planar, plane, angle, name="draft")

    @staticmethod
    def _do_draft(faces: list, plane: Any, angle: float) -> Any:
        return draft(faces, neutral_plane=plane, angle=angle)

    def draft_variable(self, solid: Any, face_angles: list, *, neutral: str,
                       neutral_offset: float = 0.0) -> Any:
        # A variable (per-face) draft tapers each planar wall by its OWN angle about one
        # neutral plane, via raw OCP BRepOffsetAPI_DraftAngle (build123d's draft is one angle
        # for all faces). Parting-line / step draft (a taper that flips across a parting
        # curve) is NOT supported: it needs a parting-curve/surface model OCCT does not expose
        # simply, so it is called out rather than faked.
        if neutral not in _PLANES:
            raise KernelOpError(
                f"draft neutral must be one of {tuple(_PLANES)}, got {neutral!r}")
        planar = [(f, a) for (f, a) in face_angles
                  if getattr(f, "geom_type", None) == GeomType.PLANE]
        if not planar:
            raise KernelOpError("variable draft found no planar faces among the selected faces")
        return self._robust(self._do_draft_variable, solid, planar, neutral, neutral_offset,
                            name="draft")

    @staticmethod
    def _do_draft_variable(solid: Any, planar: list, neutral: str,
                           neutral_offset: float) -> Any:
        from build123d import Solid
        base = _PLANES[neutral].offset(neutral_offset)
        origin = base.origin
        pull = base.z_dir
        gp_neutral = gp_Pln(gp_Pnt(origin.X, origin.Y, origin.Z),
                            gp_Dir(pull.X, pull.Y, pull.Z))
        pull_dir = gp_Dir(pull.X, pull.Y, pull.Z)
        maker = BRepOffsetAPI_DraftAngle(solid.wrapped)
        for face, angle in planar:
            maker.Add(face.wrapped, pull_dir, math.radians(angle), gp_neutral)
        maker.Build()
        return Solid(maker.Shape())

    def thread_cut(self, solid: Any, *, axis_point: Point3, axis_dir: Point3,
                   major_d: float, pitch: float, length: float, internal: bool) -> Any:
        if pitch <= 0.0:
            raise KernelOpError(f"thread pitch must be positive; got {pitch}")
        return self._robust(self._do_thread_cut, solid, axis_point, axis_dir, major_d,
                            pitch, length, internal, name="thread")

    @staticmethod
    def _do_thread_cut(solid: Any, axis_point: Point3, axis_dir: Point3, major_d: float,
                       pitch: float, length: float, internal: bool) -> Any:
        from build123d import Polygon, Solid
        # A modeled thread: sweep a V profile along a helix built DIRECTLY on the target axis
        # (Helix center + direction), then boolean it with the solid. Building the helix in
        # place avoids a fragile Plane-based relocation of the swept tool (that mapping left
        # the tool mis-placed so the cut removed nothing). The profile plane is derived from
        # the helix start tangent so the profile stays radially oriented turn to turn, cutting
        # a consistent-depth groove.
        radius = major_d / 2.0
        helix = Helix(pitch=pitch, height=length, radius=radius, center=tuple(axis_point),
                      direction=tuple(axis_dir))
        pplane = Plane(origin=helix @ 0, z_dir=helix % 0)
        # ISO 60-degree V groove: the triangle BASE spans one pitch at (just beyond) the crest
        # surface; the APEX points INWARD to the root (~0.61*pitch deep). In the profile plane
        # +x is the outward radial direction, so the apex x is negative and the base x is a
        # small positive crest overshoot.
        depth = 0.61 * pitch
        crest = 0.05 * pitch
        tri = pplane * Polygon((crest, -pitch / 2.0), (-depth, 0.0), (crest, pitch / 2.0),
                               align=None)
        # is_frenet=True locks the profile to the helix Frenet frame so its normal always
        # points at the axis; every turn then cuts to the SAME depth (measured: constant 0.364
        # vs a plain sweep's 0.08..0.55 wander, which is the ragged-thread artifact). This is
        # only correct because the helix is built in-place on the target axis (an earlier bug
        # relocated a plain-swept tool with a Plane mapping, which made frenet miss the cut).
        tool = sweep(tri, path=helix, is_frenet=True)  # pyrefly: ignore[bad-argument-type]
        result = solid - tool if not internal else solid + tool
        return result if isinstance(result, Solid) else Solid(result.wrapped)

    def wrap(self, solid: Any, face: Any, *, text: str | None = None,
             profile: Any = None, font_size: float = 5.0, font: str = "Arial",
             font_style: str = "regular", depth: float = 1.0, mode: str = "emboss",
             offset: Point2 = (0.0, 0.0), rotation: float = 0.0) -> Any:
        return self._robust(self._do_wrap, solid, face, text, profile, font_size, font,
                            font_style, depth, mode, offset, rotation, name="wrap")

    @staticmethod
    def _do_wrap(solid: Any, face: Any, text: str | None, profile: Any, font_size: float,
                 font: str, font_style: str, depth: float, mode: str,
                 offset: Point2, rotation: float) -> Any:
        # text builds glyphs (multi-line if it contains newlines); otherwise the profile is a
        # prewrapped 2D face. A missing font falls back to the default (logged). emboss adds
        # OUTWARD by depth; engrave cuts INWARD by depth.
        style = _FONT_STYLES.get(font_style, FontStyle.REGULAR)
        shape2d = (Text(text, font_size=font_size, font=_resolve_font(font), font_style=style)
                   if text is not None else profile)
        if face.geom_type in (GeomType.CYLINDER, GeomType.CONE):
            return _wrap_curved(solid, face, shape2d, offset, rotation, depth, mode)
        # Flat face: place on the face's plane (offset u/v, in-plane rotation) and extrude.
        # The Plane * Pos * Rot * sketch placement is the untyped build123d/OCP boundary.
        placed = Plane(face) * Pos(offset[0], offset[1]) * Rot(0, 0, rotation) * shape2d  # pyrefly: ignore[unsupported-operation]
        if mode == "emboss":
            return solid + extrude(placed, amount=abs(depth))  # pyrefly: ignore[bad-argument-type]
        return solid - extrude(placed, amount=-abs(depth))  # pyrefly: ignore[bad-argument-type]

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

    def describe_elements(self, solid: Any) -> list:
        # Describe per body and tag each descriptor with its body_id: a single shape is one
        # implicit body ("body/0"); a BodySet's descriptors carry each body's own id, so a
        # face reference resolves within its body (per-body addressability).
        described: list = []
        for body in self.bodies(solid):
            for descriptor in self._describe_one(body.shape):
                descriptor["body_id"] = body.id
                described.append(descriptor)
        return described

    def axis_of(self, face: Any) -> dict | None:
        from OCP.BRepAdaptor import BRepAdaptor_Surface  # pyrefly: ignore[missing-module-attribute]
        from OCP.GeomAbs import GeomAbs_Cylinder  # pyrefly: ignore[missing-module-attribute]

        wrapped = face.wrapped if hasattr(face, "wrapped") else face
        adaptor = BRepAdaptor_Surface(wrapped)
        if adaptor.GetType() != GeomAbs_Cylinder:
            return None
        cylinder = adaptor.Cylinder()
        axis = cylinder.Axis()
        loc = axis.Location()
        direction = axis.Direction()
        return {"location": (loc.X(), loc.Y(), loc.Z()),
                "direction": (direction.X(), direction.Y(), direction.Z()),
                "radius": cylinder.Radius()}

    @staticmethod
    def _describe_one(solid: Any) -> list:
        """Face then edge descriptors for one body's shape (no body_id yet)."""
        described: list = []
        for face in solid.faces():
            described.append(_describe_face(face))
        for edge in solid.edges():
            described.append(_describe_edge(edge))
        return described

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
    def _do_fillet_variable(solid: Any, edges: list, radius_start: float,
                            radius_end: float) -> Any:
        # A radius that ramps r_start -> r_end along each edge, via raw OCP
        # BRepFilletAPI_MakeFillet.Add(r1, r2, edge) (build123d's fillet is constant-radius
        # only). This is the NX/Creo/Fusion variable-radius fillet.
        from build123d import Solid
        maker = BRepFilletAPI_MakeFillet(solid.wrapped)
        for edge in edges:
            maker.Add(radius_start, radius_end, edge.wrapped)
        maker.Build()
        return Solid(maker.Shape())

    @staticmethod
    def _do_chamfer(solid: Any, edges: list, distance: float,
                    distance2: float | None) -> Any:
        # distance2 None >> symmetric; set >> two-distance. build123d-native either way.
        return solid.chamfer(distance, distance2, edges)

    @staticmethod
    def _do_chamfer_angle(solid: Any, edges: list, distance: float, angle: float) -> Any:
        # Per-edge distance-angle via raw OCP: each edge gets its own auto-picked adjacent
        # face (the first face sharing the edge) as the angle reference. build123d's
        # chamfer cannot do this (it requires all edges on one reference face).
        occ_solid = solid.wrapped
        edge_to_faces = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(occ_solid, TopAbs_EDGE, TopAbs_FACE, edge_to_faces)
        maker = BRepFilletAPI_MakeChamfer(occ_solid)
        for edge in edges:
            faces = edge_to_faces.FindFromKey(edge.wrapped)
            face = TopoDS.Face_s(faces.First())
            maker.AddDA(distance, math.radians(angle), edge.wrapped, face)
        maker.Build()
        from build123d import Solid
        return Solid(maker.Shape())

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
        return self._as_single_shape(result)

    @staticmethod
    def _as_single_shape(result: Any) -> Any:
        """Normalize a multi-body result (ShapeList) into one shape.

        A boolean can split a body into disjoint pieces, returning a ShapeList; the rest
        of the pipeline (volume, edges, export) expects a single shape, so wrap the parts
        in one Compound. A single shape passes through unchanged.
        """
        if isinstance(result, (list, tuple)) or type(result).__name__ == "ShapeList":
            from build123d import Compound

            members = list(result)
            return members[0] if len(members) == 1 else Compound(children=members)
        return result

    @staticmethod
    def _is_valid(shape: Any) -> bool:
        """Whether ``shape`` is a valid B-rep result.

        A boolean/dress-up op may return a single solid, a Compound, or a ShapeList of
        several solids (e.g. a cut that splits a body). ShapeList has no ``is_valid``, so
        validate each of its members; a single shape uses its ``is_valid`` (a property in
        build123d, tolerated as a callable across versions). An empty result is invalid.
        """
        if isinstance(shape, (list, tuple)) or type(shape).__name__ == "ShapeList":
            members = list(shape)
            return bool(members) and all(Build123dKernel._is_valid(m) for m in members)
        flag = getattr(shape, "is_valid", None)
        if flag is None:
            return True
        return bool(flag() if callable(flag) else flag)

    def version(self) -> str:
        b123d = importlib.metadata.version("build123d")
        ocp = importlib.metadata.version("cadquery-ocp")
        return f"build123d={b123d};ocp={ocp}"

    def signature(self, solid: Any) -> dict:
        if isinstance(solid, BodySet):
            # Per-body signatures, ordered by a deterministic key (body id, then volume, then
            # bbox) so the multibody signature is independent of kernel body ordering. A
            # single-body part never reaches here, so its signature is the flat dict, as before.
            per_body = [(b.id, self.signature(b.shape)) for b in solid.bodies]
            per_body.sort(key=lambda p: (p[0], p[1]["volume"], p[1]["bbox"]))
            return {"bodies": [sig for _, sig in per_body]}
        faces = solid.faces()
        edges = solid.edges()
        vertices = solid.vertices()
        box = solid.bounding_box()
        cog = solid.center(CenterOf.MASS)
        return {
            "counts": {"face": len(faces), "edge": len(edges), "vertex": len(vertices)},
            "surface_types": _type_histogram(faces),
            "curve_types": _type_histogram(edges),
            "volume": solid.volume,
            "area": solid.area,
            "bbox": (tuple(box.min), tuple(box.max)),
            "cog": (cog.X, cog.Y, cog.Z),
        }

    def bodies(self, shape: Any) -> list:
        # A BodySet exposes its bodies; any other shape is a single implicit solid body.
        if isinstance(shape, BodySet):
            return shape.bodies
        return [Body(id="body/0", kind="solid", shape=shape, created_by="")]

    def union_bodies(self, shapes: list, *, origin: str, sources: list | None = None) -> Any:
        return union_bodies(shapes, origin, sources)

    def transform(self, shape: Any, *, move: Point3 = (0.0, 0.0, 0.0),
                  rotate: dict | None = None, scale: Any = None) -> Any:
        # Apply scale >> rotate >> move in that fixed order (deterministic and unambiguous).
        # Rigid move/rotate are exact; non-uniform scale can produce an invalid B-rep, so it
        # is gated by _robust. Uniform scale and the rigid stages are not gated.
        # A multibody running shape transforms per body, ids preserved (like mirror/split);
        # build123d Shape ops (moved/rotate/scale) do not exist on a BodySet.
        if isinstance(shape, BodySet):
            moved = [Body(id=b.id, kind=b.kind,
                          shape=self.transform(b.shape, move=move, rotate=rotate, scale=scale),
                          created_by=b.created_by) for b in shape.bodies]
            return BodySet(moved)
        result = shape
        if scale is not None:
            if isinstance(scale, (int, float)):
                result = result.scale(float(scale))
            else:
                result = self._robust(self._do_gscale, result, scale, name="scale")
        if rotate is not None:
            axis = Axis(tuple(rotate.get("about", (0.0, 0.0, 0.0))),
                        tuple(rotate["axis"]))  # pyrefly: ignore[no-matching-overload]
            result = result.rotate(axis, float(rotate["angle"]))
        if tuple(move) != (0.0, 0.0, 0.0):
            result = result.moved(Location(tuple(move)))  # pyrefly: ignore[no-matching-overload]
        return result

    def mirror(self, shape: Any, *, plane: dict) -> Any:
        # A reflection flips handedness and inverts face orientation; build123d's Shape.mirror
        # corrects orientation and returns a valid solid, so it is preferred over a negative
        # scale through transform. Gated by _robust like the other B-rep-mutating ops.
        if isinstance(shape, BodySet):
            reflected = [Body(id=b.id, kind=b.kind,
                              shape=self.mirror(b.shape, plane=plane),
                              created_by=b.created_by) for b in shape.bodies]
            return BodySet(reflected)
        mirror_plane = self._mirror_plane(plane)
        return self._robust(self._do_mirror, shape, mirror_plane, name="mirror")

    @staticmethod
    def _mirror_plane(plane: dict) -> Any:
        """Resolve the normalized plane description to a build123d Plane."""
        if plane["kind"] == "base":
            return _PLANES[plane["plane"]].offset(float(plane["offset"]))
        # build123d Plane names the normal `z_dir` (not `normal`).
        return Plane(origin=tuple(plane["point"]),
                     z_dir=tuple(plane["z_dir"]))  # pyrefly: ignore[no-matching-overload]

    @staticmethod
    def _do_mirror(shape: Any, mirror_plane: Any) -> Any:
        """The raw reflection (wrapped by _robust)."""
        return shape.mirror(mirror_plane)

    def split(self, shape: Any, *, plane: dict, keep: str) -> list:
        # build123d Shape.split(plane, keep=Keep.BOTH) returns a (top, bottom) tuple; TOP is
        # the +normal side. TOP/BOTTOM return one solid. _robust validates a SINGLE shape and
        # cannot check a tuple, so the both-case splits directly (build123d returns valid
        # solids, verified) and only the single-side path is _robust-gated.
        split_plane = self._mirror_plane(plane)
        if keep == "both":
            top, bottom = shape.split(split_plane, keep=Keep.BOTH)
            return [top, bottom]
        result = self._robust(self._do_split, shape, split_plane, _KEEP[keep], name="split")
        return [result]

    @staticmethod
    def _do_split(shape: Any, split_plane: Any, keep_enum: Any) -> Any:
        """The raw single-side split (wrapped by _robust)."""
        return shape.split(split_plane, keep=keep_enum)

    @staticmethod
    def _do_gscale(shape: Any, scale: Any) -> Any:
        # Non-uniform scale via raw OCP gp_GTrsf (build123d scale is uniform only).
        g = gp_GTrsf()
        g.SetValue(1, 1, float(scale[0]))
        g.SetValue(2, 2, float(scale[1]))
        g.SetValue(3, 3, float(scale[2]))
        return Solid(BRepBuilderAPI_GTransform(shape.wrapped, g, True).Shape())

    def volume(self, solid: Any) -> float:
        if isinstance(solid, BodySet):
            return sum(self.volume(b.shape) for b in solid.bodies)
        return solid.volume

    def bounding_box(self, solid: Any) -> Bounds:
        if isinstance(solid, BodySet):
            boxes = [self.bounding_box(b.shape) for b in solid.bodies]
            lows = [b[0] for b in boxes]
            highs = [b[1] for b in boxes]
            return ((min(x for x, _, _ in lows), min(y for _, y, _ in lows),
                     min(z for _, _, z in lows)),
                    (max(x for x, _, _ in highs), max(y for _, y, _ in highs),
                     max(z for _, _, z in highs)))
        box = solid.bounding_box()
        return (tuple(box.min), tuple(box.max))

    def place(self, shape: Any, matrix: list[list[float]]) -> Any:
        """Place a solid by a row-major 4x4 rigid matrix (assembly placement convention)."""
        return Location(_trsf_from(matrix)) * shape

    def distance(self, shape_a: Any, shape_b: Any) -> float:
        """Minimum distance between two solids via BRepExtrema_DistShapeShape (mm)."""
        calc = BRepExtrema_DistShapeShape(_wrapped(shape_a), _wrapped(shape_b))
        calc.Perform()
        return float(calc.Value())

    def common_volume(self, shape_a: Any, shape_b: Any) -> float:
        """Volume of the boolean intersection (mm^3); 0.0 when disjoint or merely touching."""
        inter = _b3d(shape_a) & _b3d(shape_b)
        return float(inter.volume) if inter is not None else 0.0

    def _export_solids(self, shape: Any) -> list:
        """(body_id, solid) per exported solid, in export order (body -> solid).

        The single source of truth for both the export Compound and mesh_body_ids, so the glTF
        primitive order and the per-primitive body-id list stay in lockstep. A body's shape is
        often a Compound (a boolean/mirror result); the glTF mesh is built from its SOLIDs.
        """
        pairs: list = []
        for body in self.bodies(shape):
            solids = body.shape.solids() if hasattr(body.shape, "solids") else [body.shape]
            for one in (solids or [body.shape]):
                pairs.append((body.id, one))
        return pairs

    def mesh_body_ids(self, shape: Any) -> list:
        # One body id per exported glTF PRIMITIVE, in export order (body -> solid -> face).
        # export_gltf tessellates one primitive per face; GLTFLoader turns each primitive into
        # its own three.js Mesh, so the viewer's pickParts is per-FACE, not per-body. This
        # parallel per-face list lets the viewer map pickParts[i] -> body -> material
        # positionally (glTF mesh NAMES do not survive GLTFLoader reliably). Small structural
        # walk (a handful of solids/faces), not a numeric loop - no vectorization to be had.
        ids: list = []
        for body_id, one in self._export_solids(shape):
            faces = one.faces() if hasattr(one, "faces") else [one]
            ids.extend(body_id for _ in faces)
        return ids

    def import_solid(self, path: str) -> Any:
        """Import a STEP/IGES solid via build123d."""
        from build123d import import_step  # pyrefly: ignore[import-error]

        return import_step(path)

    def defeature(self, solid: Any, face: Any) -> Any:
        return self._robust(self._do_defeature, solid, face, name="defeature")

    def _do_defeature(self, solid: Any, face: Any) -> Any:
        wrapped = solid.wrapped if hasattr(solid, "wrapped") else solid
        target = face.wrapped if hasattr(face, "wrapped") else face
        remove = TopTools_ListOfShape()
        remove.Append(target)
        defeat = BRepAlgoAPI_Defeaturing()
        defeat.SetShape(wrapped)
        defeat.AddFacesToRemove(remove)
        defeat.Build()
        return Solid(defeat.Shape())

    def move_face(self, solid: Any, face: Any, distance: float) -> Any:
        return self._robust(self._do_move_face, solid, face, distance, name="move_face")

    def _do_move_face(self, solid: Any, face: Any, distance: float) -> Any:
        # Synthesize move_face (OCCT has no native op): extrude the target face into a slab along
        # its normal, then fuse it on (outward, distance >= 0) or cut it away (inward). Use the
        # private _do_ boolean forms since this is already inside a _robust wrapper (one failure
        # surface, no double validation).
        target = face if hasattr(face, "normal_at") else Face(face)
        normal = target.normal_at()
        slab = Solid.extrude(target, normal * distance)
        if distance >= 0:
            return self._do_fuse([solid, slab])
        return self._do_cut(solid, [slab])

    def offset_solid(self, solid: Any, distance: float) -> Any:
        return self._robust(self._do_offset_solid, solid, distance, name="offset")

    def _do_offset_solid(self, solid: Any, distance: float) -> Any:
        one = solid.solids()[0] if hasattr(solid, "solids") else solid
        # offset_3d(openings, thickness): no openings (closed offset), positional thickness.
        return one.offset_3d(None, distance)

    def _edge_face_map(self, solid: Any) -> Any:
        wrapped = solid.wrapped if hasattr(solid, "wrapped") else solid
        edge_faces = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(wrapped, TopAbs_EDGE, TopAbs_FACE, edge_faces)
        return edge_faces

    def face_neighbours(self, solid: Any, face: Any) -> list[Any]:
        # Faces sharing any edge with `face`, via the edge -> ancestor-faces map.
        target = face.wrapped if hasattr(face, "wrapped") else face
        edge_faces = self._edge_face_map(solid)
        neighbours: list[Any] = []
        explorer = TopExp_Explorer(target, TopAbs_EDGE)
        while explorer.More():
            for candidate in list(edge_faces.FindFromKey(explorer.Current())):
                if not candidate.IsSame(target) and not any(candidate.IsSame(n)
                                                            for n in neighbours):
                    neighbours.append(candidate)
            explorer.Next()
        return neighbours

    def is_tangent_adjacent(self, solid: Any, face: Any) -> bool:
        # G1 (tangent) stored continuity across a shared edge means defeature silently no-ops
        # there (4.0 envelope). OCCT stores G1 on fillet/blend seams, which is exactly the case
        # we must refuse.
        target = face.wrapped if hasattr(face, "wrapped") else face
        edge_faces = self._edge_face_map(solid)
        tangent_floor = int(GeomAbs_G1)
        explorer = TopExp_Explorer(target, TopAbs_EDGE)
        while explorer.More():
            ancestors = list(edge_faces.FindFromKey(explorer.Current()))
            edge = TopoDS.Edge_s(explorer.Current())
            for candidate in ancestors:
                if candidate.IsSame(target):
                    continue
                continuity = BRep_Tool.Continuity_s(edge, TopoDS.Face_s(target),
                                                    TopoDS.Face_s(candidate))
                if int(continuity) >= tangent_floor:
                    return True
            explorer.Next()
        return False

    def min_wall_thickness(self, solid: Any) -> float | None:
        # A cheap, safe lower-bound estimate: the smallest bounding-box dimension. A finer
        # medial-axis estimate is a follow-up; the guard only needs a conservative floor to
        # refuse inward offsets that would exceed the wall.
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        span = min(maxx - minx, maxy - miny, maxz - minz)
        return span if span > 0 else None

    def history(self, inputs: list[Any], output: Any) -> ElementHistory:
        """Report output lineage. Extrude is instrumented; other ops report empty for now.

        build123d hides the prism builder, so this uses a coarse but correct lineage for a
        single-profile extrude: every output face descends from the profile face(s). That is
        enough for deterministic persistent naming and carried-face survival; finer per-op
        lineage (real BRepTools_History wired through each op) is a logged follow-up.
        """
        history = ElementHistory()
        if not inputs:
            return history
        input_handles: list[Any] = []
        for shape in inputs:
            input_handles.extend(d["handle"] for d in self.describe_elements(shape))
        for descriptor in self.describe_elements(output):
            if descriptor["kind"] == "face":
                history.generated_from[descriptor["handle"]] = list(input_handles)
        return history

    def export(self, solid: Any, path: str) -> None:
        if isinstance(solid, BodySet):
            # A multibody part exports as a compound: STEP as a multi-solid assembly, glTF as
            # one mesh per body solid, in body order (parallel to mesh_body_ids via the shared
            # _export_solids). Single-shape export is unchanged.
            from build123d import Compound
            solid = Compound(children=[one for _bid, one in self._export_solids(solid)])
        lowered = path.lower()
        if lowered.endswith(".glb"):
            export_gltf(solid, path, unit=Unit.MM, binary=True,
                        linear_deflection=self._deflection(solid),
                        angular_deflection=_ANGULAR_DEFLECTION)
        elif lowered.endswith(".gltf"):
            export_gltf(solid, path, unit=Unit.MM, binary=False,
                        linear_deflection=self._deflection(solid),
                        angular_deflection=_ANGULAR_DEFLECTION)
        elif lowered.endswith((".step", ".stp")):
            export_step(solid, path, unit=Unit.MM)
        elif lowered.endswith(".stl"):
            export_stl(solid, path)
        else:
            raise ValueError(
                f"unsupported export format for {path!r}; expected .gltf/.glb/.step/.stp/.stl"
            )
        logger.debug("exported solid to %s", path)

    def export_assembly(self, components: list[dict], path: str) -> None:
        """Structured AP242 STEP via XCAF/XDE: one label per part (name+color), instances as
        located components under a root assembly. See _write_step_assembly for the verified XCAF
        recipe (UpdateAssemblies before write is REQUIRED, else the output is a flat shape)."""
        _write_step_assembly(components, path)
        logger.debug("exported assembly (%d components) to %s", len(components), path)

    def _deflection(self, solid: Any) -> float:
        """Tessellation linear deflection scaled to the model size (design §4a, §13).

        build123d's default (0.001 mm ABSOLUTE) is a relative ~1e-4 on a small curved
        part, which explodes the triangle count (a helical coil took ~70s / 8 MB). A
        deflection of 0.2% of the bounding-box diagonal, paired with the angular deflection
        that governs cross-section smoothness, keeps the mesh smooth while fast (that coil
        drops to ~1s / 1.5 MB) and is size-relative so it is stable across model scales
        (the pinned tessellation deflection the goldens assume).
        """
        (x0, y0, z0), (x1, y1, z1) = self.bounding_box(solid)
        diagonal = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
        return max(diagonal * 0.002, 1e-4)


def _describe_face(face: Any) -> dict:
    """Face descriptor from a build123d Face."""
    center = face.center()
    normal = face.normal_at()
    box = face.bounding_box()
    descriptor = {
        "kind": "face", "handle": face, "geom_type": _geom_name(face),
        "normal": (round(normal.X, 9), round(normal.Y, 9), round(normal.Z, 9)),
        "area": face.area,
        "center": (center.X, center.Y, center.Z),
        "min_z": box.min.Z, "mid_z": center.Z, "max_z": box.max.Z,
    }
    _add_axis_fields(descriptor, face)
    return descriptor


def _add_axis_fields(descriptor: dict, face: Any) -> None:
    # Cylindrical faces carry their axis so coaxial/tangent relations can read it from attrs.
    if _geom_name(face) != "cylinder":
        return
    from OCP.BRepAdaptor import BRepAdaptor_Surface  # pyrefly: ignore[missing-module-attribute]

    adaptor = BRepAdaptor_Surface(face.wrapped)
    cylinder = adaptor.Cylinder()
    axis = cylinder.Axis()
    loc, direction = axis.Location(), axis.Direction()
    descriptor["axis_location"] = (loc.X(), loc.Y(), loc.Z())
    descriptor["axis_direction"] = (direction.X(), direction.Y(), direction.Z())
    descriptor["radius"] = cylinder.Radius()


def _describe_edge(edge: Any) -> dict:
    """Edge descriptor from a build123d Edge (orientation rule matches edges_of)."""
    p0, p1 = edge.position_at(0), edge.position_at(1)
    direction = p1 - p0
    vertical = (abs(direction.Z) > 1e-6 and abs(direction.X) < 1e-6
                and abs(direction.Y) < 1e-6)
    mid = edge.position_at(0.5)
    box = edge.bounding_box()
    return {
        "kind": "edge", "handle": edge, "geom_type": _geom_name(edge),
        "length": edge.length,
        "center": (mid.X, mid.Y, mid.Z),
        "orientation": "vertical" if vertical else "horizontal",
        "min_z": box.min.Z, "mid_z": mid.Z, "max_z": box.max.Z,
    }


def _geom_name(shape: Any) -> str:
    """Lower-cased geometry-type name (e.g. 'plane', 'cylinder', 'line')."""
    geom_type = getattr(shape, "geom_type", None)
    if geom_type is None:
        return "other"
    name = getattr(geom_type, "name", str(geom_type))
    return str(name).lower()


def _ellipse_angle_degrees(cx: float, cy: float, mx: float, my: float,
                           px: float, py: float) -> float:
    """Parametric angle (degrees) of point (px,py) about an ellipse frame.

    The frame's X axis points from center (cx,cy) to the major-axis end (mx,my). The angle is
    measured in that frame (0 deg at the major-axis end), which is the convention
    ``Edge.make_ellipse`` uses for ``start_angle`` / ``end_angle``.
    """
    ax, ay = mx - cx, my - cy
    axis_angle = math.atan2(ay, ax)
    point_angle = math.atan2(py - cy, px - cx)
    return math.degrees((point_angle - axis_angle) % (2.0 * math.pi))


def _gp_pnt(basis: Any, x: float, y: float) -> Any:
    """A gp_Pnt for sketch-plane point (x, y) placed in world coords on ``basis``."""
    v = basis.from_local_coords(Vector(x, y, 0))
    return gp_Pnt(v.X, v.Y, v.Z)


def _build_edge(edge: dict, basis: Any) -> Any:
    """Build a build123d Edge from a sketch edge descriptor on the ``basis`` plane."""
    kind = edge["kind"]
    if kind == "line":
        (ax, ay), (bx, by) = edge["points"]
        a = basis.from_local_coords(Vector(ax, ay, 0))
        b = basis.from_local_coords(Vector(bx, by, 0))
        return Edge.make_line(a, b)  # pyrefly: ignore[bad-argument-type]
    if kind == "arc":
        (sx, sy), (mx, my), (ex, ey) = edge["points"]
        start = basis.from_local_coords(Vector(sx, sy, 0))
        mid = basis.from_local_coords(Vector(mx, my, 0))
        end = basis.from_local_coords(Vector(ex, ey, 0))
        return Edge.make_three_point_arc(start, mid, end)  # pyrefly: ignore[bad-argument-type]
    if kind == "circle":
        cx, cy = edge["center"]
        origin = basis.from_local_coords(Vector(cx, cy, 0))
        face_plane = Plane(origin=origin, z_dir=basis.z_dir)  # pyrefly: ignore[no-matching-overload]
        return Edge.make_circle(edge["radius"], face_plane)
    if kind in ("bezier", "spline"):
        pts = [basis.from_local_coords(Vector(x, y, 0)) for (x, y) in edge["points"]]
        # bezier: control points (curve passes through first/last, pulled toward interior).
        # spline (the interpolated entity): the curve passes through every point.
        if kind == "bezier":
            return Edge.make_bezier(*pts)  # pyrefly: ignore[bad-argument-type]
        return Edge.make_spline(pts)  # pyrefly: ignore[bad-argument-type]
    if kind in ("ellipse", "ellipse_arc"):
        cx, cy = edge["center"]
        mx, my = edge["major_axis_end"]
        x_radius = math.hypot(mx - cx, my - cy)
        y_radius = float(edge["minor_radius"])
        origin = basis.from_local_coords(Vector(cx, cy, 0))
        major_dir = basis.from_local_coords(Vector(mx, my, 0)) - origin
        frame = Plane(origin=origin, x_dir=major_dir, z_dir=basis.z_dir)  # pyrefly: ignore[no-matching-overload]
        if kind == "ellipse":
            return Edge.make_ellipse(x_radius, y_radius, frame)  # pyrefly: ignore[bad-argument-type]
        (sx, sy), (ex, ey) = edge["points"]
        start_angle = _ellipse_angle_degrees(cx, cy, mx, my, sx, sy)
        end_angle = _ellipse_angle_degrees(cx, cy, mx, my, ex, ey)
        return Edge.make_ellipse(  # pyrefly: ignore[bad-argument-type]
            x_radius, y_radius, frame, start_angle=start_angle, end_angle=end_angle)
    if kind == "conic":
        (sx, sy), (apx, apy), (ex, ey) = edge["points"]
        rho = float(edge["rho"])
        # Rational quadratic Bezier: 3 control poles with the apex weighted rho/(1-rho); the
        # curve passes through start/end (weight 1) and bows toward the apex. rho<0.5 traces an
        # ellipse arc, =0.5 a parabola, >0.5 a hyperbola (the reference-tool conic model).
        poles = TColgp_Array1OfPnt(1, 3)
        poles.SetValue(1, _gp_pnt(basis, sx, sy))
        poles.SetValue(2, _gp_pnt(basis, apx, apy))
        poles.SetValue(3, _gp_pnt(basis, ex, ey))
        weights = TColStd_Array1OfReal(1, 3)
        weights.SetValue(1, 1.0)
        weights.SetValue(2, rho / (1.0 - rho))
        weights.SetValue(3, 1.0)
        curve = Geom_BezierCurve(poles, weights)
        return Edge(BRepBuilderAPI_MakeEdge(curve).Edge())  # pyrefly: ignore[bad-argument-type]
    raise ValueError(f"unknown sketch edge kind {kind!r}")


def _project_edge(edge: Any, basis: Any) -> dict:
    """Project one build123d edge onto ``basis`` plane, returning a 2D descriptor."""
    name = _geom_name(edge)
    if name == "circle":
        center = basis.to_local_coords(edge.arc_center)
        return {"kind": "circle", "center": (center.X, center.Y),
                "radius": float(edge.radius)}
    if name in ("bspline", "bezier"):
        # Projecting a curved (spline/bezier) edge into a 2D descriptor is deferred: OCCT
        # hands back a BSpline we do not decompose, and no current feature projects a
        # spline. Fail loudly rather than silently mangling the curve into a line.
        raise NotImplementedError(
            "projecting spline/bezier edges onto a sketch plane is not yet supported")
    a = basis.to_local_coords(edge.position_at(0))
    b = basis.to_local_coords(edge.position_at(1))
    pa, pb = (a.X, a.Y), (b.X, b.Y)
    if abs(pa[0] - pb[0]) < 1e-9 and abs(pa[1] - pb[1]) < 1e-9:
        return {"kind": "degenerate"}
    if name == "arc":
        mid = basis.to_local_coords(edge.position_at(0.5))
        return {"kind": "arc", "points": [pa, (mid.X, mid.Y), pb]}
    return {"kind": "line", "points": [pa, pb]}


def _type_histogram(shapes: list) -> dict:
    """Count shapes by lower-cased geometry-type name."""
    histogram: dict = {}
    for shape in shapes:
        name = _geom_name(shape)
        histogram[name] = histogram.get(name, 0) + 1
    return histogram


def _thin_ring(face: Any, thin: float) -> Any:
    """A wall-thick ring: the face minus its inward offset by ``thin`` (a hollow profile)."""
    inner = offset(face, amount=-abs(thin))  # pyrefly: ignore[no-matching-overload]
    return face - inner


def _wrapped(shape: Any) -> Any:
    """The OCP TopoDS_Shape for a build123d object or an already-wrapped shape."""
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def _b3d(shape: Any) -> Any:
    """A build123d Solid for boolean ops, from a build123d object or a wrapped TopoDS_Shape."""
    from build123d import Solid
    return shape if hasattr(shape, "wrapped") else Solid(shape)


def _write_step_assembly(components: list[dict], path: str) -> None:
    """Build an XCAFDoc assembly from components + write AP242. OCP/XCAF boundary (Any-typed)."""
    from OCP.Interface import Interface_Static  # pyrefly: ignore[missing-module-attribute]
    from OCP.Quantity import (
        Quantity_Color,  # pyrefly: ignore[missing-module-attribute]
        Quantity_TOC_RGB,  # pyrefly: ignore[missing-module-attribute]
    )
    from OCP.STEPCAFControl import (
        STEPCAFControl_Writer,  # pyrefly: ignore[missing-module-attribute]
    )
    from OCP.TCollection import (
        TCollection_ExtendedString,  # pyrefly: ignore[missing-module-attribute]
    )
    from OCP.TDataStd import TDataStd_Name  # pyrefly: ignore[missing-module-attribute]
    from OCP.TDocStd import TDocStd_Document  # pyrefly: ignore[missing-module-attribute]
    from OCP.TopLoc import TopLoc_Location  # pyrefly: ignore[missing-module-attribute]
    from OCP.XCAFApp import XCAFApp_Application  # pyrefly: ignore[missing-module-attribute]
    from OCP.XCAFDoc import (
        XCAFDoc_ColorType,  # pyrefly: ignore[missing-module-attribute]
        XCAFDoc_DocumentTool,  # pyrefly: ignore[missing-module-attribute]
    )

    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))
    app.InitDocument(doc)
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    root = shape_tool.NewShape()
    TDataStd_Name.Set_s(root, TCollection_ExtendedString("assembly"))
    part_labels: dict[str, Any] = {}  # name -> part label (dedup parts sharing a name)
    for comp in components:
        name = comp["name"]
        label = part_labels.get(name)
        if label is None:
            label = shape_tool.AddShape(_wrapped(comp["shape"]), False)
            TDataStd_Name.Set_s(label, TCollection_ExtendedString(name))
            color = comp.get("color")
            if color is not None:
                color_tool.SetColor(
                    label,
                    Quantity_Color(float(color[0]), float(color[1]), float(color[2]),
                                   Quantity_TOC_RGB),
                    XCAFDoc_ColorType.XCAFDoc_ColorGen)
            part_labels[name] = label
        shape_tool.AddComponent(root, label, TopLoc_Location(_trsf_from(comp["placement"])))
    # REQUIRED: without UpdateAssemblies the writer emits a flat shape, not an assembly tree.
    shape_tool.UpdateAssemblies()
    Interface_Static.SetCVal_s("write.step.schema", "AP242")
    writer = STEPCAFControl_Writer()
    writer.Transfer(doc)
    writer.Write(path)


def _trsf_from(matrix: list[list[float]]) -> Any:
    """A gp_Trsf from a row-major 4x4 (rotation top-left, translation in the last row).

    Our convention maps a point as ``p' = p . R + t`` (translation in row 3), while
    ``gp_Trsf.SetValues`` expects the column-vector form ``p' = M . p``; so the rotation passed is
    the TRANSPOSE of our R (note the ``matrix[j][i]`` order) and the translation is our last row.
    """
    from OCP.gp import gp_Trsf  # pyrefly: ignore[missing-module-attribute]
    t = gp_Trsf()
    t.SetValues(matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],
                matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],
                matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2])
    return t
