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
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_GTransform,  # pyrefly: ignore[missing-module-attribute]
)
from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer  # pyrefly: ignore[missing-module-attribute]
from OCP.gp import gp_GTrsf  # pyrefly: ignore[missing-module-attribute]
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE  # pyrefly: ignore[missing-module-attribute]
from OCP.TopExp import TopExp  # pyrefly: ignore[missing-module-attribute]
from OCP.TopoDS import TopoDS  # pyrefly: ignore[missing-module-attribute]
from OCP.TopTools import (
    TopTools_IndexedDataMapOfShapeListOfShape,  # pyrefly: ignore[missing-module-attribute]
)

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet, union_bodies
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


class Build123dKernel(Kernel):
    """build123d-backed kernel. Shapes are build123d ``Face``/``Solid`` objects."""

    def polygon_face(self, points: list[Point2], plane: str, offset: float = 0.0) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        # offset shifts the base plane along its normal; default 0.0 keeps prior behavior.
        basis = _PLANES[plane].offset(offset)
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
             end_point: Point3 | None = None) -> Any:
        # A vertex cap is a zero-area point section: build123d loft accepts Vertex in the
        # section list, giving a cone-like end. Order matters: caps bracket the faces.
        ordered: list = []
        if start_point is not None:
            ordered.append(Vertex(*start_point))
        ordered.extend(sections)
        if end_point is not None:
            ordered.append(Vertex(*end_point))
        return loft(ordered, ruled=ruled)

    def rib(self, wire: Any, *, thickness: float, depth: float) -> Any:
        # Planar-first (robust): thicken the open wire IN ITS OWN PLANE with trace into a
        # closed ribbon face, then extrude that face by depth. This avoids OCCT's fragile
        # offset/thicken-a-shell path (design.md: BRepOffsetAPI_MakeOffsetShape fails on C0
        # splines and past the smallest concave radius). thickness is symmetric about the
        # curve (trace); depth grows one direction normal to the sketch plane.
        ribbon = trace(wire, line_width=thickness)
        # A ribbon traced around a curved wire is planar but build123d cannot infer the
        # extrude direction from it, so pass the ribbon face's normal explicitly.
        normal = ribbon.faces()[0].normal_at()  # pyrefly: ignore[bad-argument-type]
        return extrude(ribbon, amount=depth, dir=normal)

    def circle_face(self, center: Point2, diameter: float, plane: str,
                    offset: float = 0.0) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane].offset(offset)
        # from_local_coords is stubbed as a wide union but returns a Vector at runtime;
        # this is the untyped-OCP boundary (see the [tool.pyrefly] note in pyproject).
        origin = basis.from_local_coords(Vector(center[0], center[1], 0))
        face_plane = Plane(origin=origin, z_dir=basis.z_dir)  # pyrefly: ignore[no-matching-overload]
        return Face(Wire(Edge.make_circle(diameter / 2.0, face_plane)))

    def wire_face(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane].offset(offset)
        occ_edges = [_build_edge(edge, basis) for edge in edges]
        return Face(Wire(occ_edges))

    def wire(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane].offset(offset)
        return Wire([_build_edge(edge, basis) for edge in edges])

    def project_edges(self, edges: list, plane: str, offset: float = 0.0) -> list:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane].offset(offset)
        return [_project_edge(edge, basis) for edge in edges]

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
        # text builds glyphs; otherwise the profile is a prewrapped 2D face. Place it on the
        # target face's plane (offset u/v, in-plane rotation). emboss extrudes OUTWARD along
        # the face normal (+depth) and adds; engrave extrudes INWARD (-depth) and cuts, so
        # the tool lands inside the material rather than floating above the surface.
        style = _FONT_STYLES.get(font_style, FontStyle.REGULAR)
        shape2d = (Text(text, font_size=font_size, font=font, font_style=style)
                   if text is not None else profile)
        # The Plane * Pos * Rot * sketch placement and extrude are the untyped build123d/OCP
        # boundary (see the [tool.pyrefly] note): correct at runtime, wide in the stubs.
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
    return {
        "kind": "face", "handle": face, "geom_type": _geom_name(face),
        "normal": (round(normal.X, 9), round(normal.Y, 9), round(normal.Z, 9)),
        "area": face.area,
        "center": (center.X, center.Y, center.Z),
        "min_z": box.min.Z, "mid_z": center.Z, "max_z": box.max.Z,
    }


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
