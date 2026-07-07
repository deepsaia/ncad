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
    Helix,
    Plane,
    Solid,
    Transition,
    Unit,
    Until,
    Vector,
    Vertex,
    Wire,
    export_gltf,
    export_step,
    export_stl,
    extrude,
    loft,
    offset,
    revolve,
    sweep,
)

from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3
from ncad.kernel.kernel_op_error import KernelOpError

logger = logging.getLogger(__name__)

_PLANES = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}
_AXES = {"X": Axis.X, "Y": Axis.Y, "Z": Axis.Z}
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

    def describe_elements(self, solid: Any) -> list:
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

    def volume(self, solid: Any) -> float:
        return solid.volume

    def bounding_box(self, solid: Any) -> Bounds:
        box = solid.bounding_box()
        return (tuple(box.min), tuple(box.max))

    def export(self, solid: Any, path: str) -> None:
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
