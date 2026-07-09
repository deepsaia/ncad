"""A lightweight, dependency-free Kernel for fast tests.

A face is modeled as its 2D point ring plus plane; a solid as (face, distance). Volume
and bounds are computed analytically for the axis-aligned extrusion cases the buckets
use. Boolean/fillet results carry a computed volume only. Not for production geometry;
enough to assert op and Builder behaviour without OCP.
"""

import math
from typing import Any

from ncad.kernel.body import Body
from ncad.kernel.body_set import BodySet, union_bodies
from ncad.kernel.kernel import Bounds, Kernel, Point2, Point3
from ncad.kernel.kernel_op_error import KernelOpError


class _FakeFace:
    """A planar polygon: its 2D point ring, the plane it lives on, and its plane offset."""

    def __init__(self, points: list[Point2], plane: str, offset: float = 0.0) -> None:
        self.points = points
        self.plane = plane
        self.offset = offset


class _FakeWireFace:
    """A face from mixed line/arc/circle edge descriptors.

    Carries the ordered endpoint ring (for bounds) and an analytic area (shoelace over
    endpoints plus each arc's circular-segment bulge; a lone circle is pi r^2).
    """

    def __init__(self, edges: list, plane: str, offset: float = 0.0) -> None:
        self.edges = edges
        self.plane = plane
        self.points = _wire_ring(edges)
        self.area = _wire_face_area(edges)
        self.offset = offset


class _FakeWire:
    """An open path: ordered edge descriptors on a plane, plus a computed length."""

    def __init__(self, edges: list, plane: str, offset: float = 0.0) -> None:
        self.edges = edges
        self.plane = plane
        self.length = _wire_length(edges)
        self.offset = offset


class _FakeSolid:
    """A face extruded by an effective distance; a wall keeps only a rim area fraction."""

    def __init__(self, face: _FakeFace, distance: float,
                 wall_area: float | None = None) -> None:
        self.face = face
        self.distance = distance
        self.wall_area = wall_area  # None = filled; else the ring area for a thin wall


class _FakeCylinder:
    """A cylinder tool: volume = pi r^2 * length; records its placement for assertions."""

    def __init__(self, center: Point3, axis: str, diameter: float, length: float) -> None:
        self.center = center
        self.axis = axis
        self.volume_val = math.pi * (diameter / 2.0) ** 2 * length


class _FakeCone:
    """A (truncated) cone tool: frustum volume pi/3 * h * (R^2 + R*r + r^2)."""

    def __init__(self, center: Point3, axis: str, bottom_diameter: float,
                 top_diameter: float, length: float) -> None:
        self.center = center
        self.axis = axis
        r = bottom_diameter / 2.0
        top_r = top_diameter / 2.0
        self.volume_val = math.pi / 3.0 * length * (r * r + r * top_r + top_r * top_r)


class _FakeCombined:
    """Result of a boolean or dress-up op: carries a computed volume and bounds.

    Downstream ops (a fillet after a hole, a chamfer after a union) still call
    ``edges_of``/``bounding_box`` on the result, so a combined shape must carry a
    bounding box, not just a volume.
    """

    def __init__(self, volume: float, bounds: Bounds) -> None:
        self.volume_val = volume
        self.bounds = bounds


class FakeKernel(Kernel):
    """In-memory kernel: analytic volume/bounds for axis-aligned extrusions."""

    def polygon_face(self, points: list[Point2], plane: str, offset: float = 0.0) -> Any:
        return _FakeFace(points, plane, offset)

    def wire_face(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        return _FakeWireFace(edges, plane, offset)

    def wire(self, edges: list, plane: str, offset: float = 0.0) -> Any:
        return _FakeWire(edges, plane, offset)

    def wire_length(self, wire: Any) -> float:
        """Path length of a fake open wire (test helper)."""
        return wire.length

    def sweep(self, profile: Any, path: Any, *, sections: list | None = None,
              guides: list | None = None, is_frenet: bool = False,
              transition: str = "transformed") -> Any:
        # Volume model: a swept solid ~ profile area x path length (a prism along the path).
        # Variable-section uses the mean of the section areas. guides/is_frenet/transition
        # do not change the analytic volume in the fake kernel. Enough for volume tests.
        if sections:
            area = sum(self._face_area(s) for s in sections) / len(sections)
        else:
            area = self._face_area(profile)
        return _FakeCombined(area * path.length, self._sweep_bounds(path))

    def loft(self, sections: list, *, ruled: bool = False,
             start_point: Point3 | None = None,
             end_point: Point3 | None = None) -> Any:
        # Prismatoid (trapezoidal) volume: sum over adjacent section pairs of
        # (A_i + A_{i+1})/2 * |offset gap|. A point cap contributes area 0 at its z.
        # ruled is a blend-shape choice, not volume-defining, so it does not change this.
        stack: list[tuple[float, float]] = []
        if start_point is not None:
            stack.append((0.0, start_point[2]))
        for face in sections:
            stack.append((self._face_area(face), face.offset))
        if end_point is not None:
            stack.append((0.0, end_point[2]))
        volume = _prismatoid_volume(stack)
        return _FakeCombined(volume, self._loft_bounds(stack))

    def _loft_bounds(self, stack: list) -> Bounds:
        """A bounds box spanning the section offset range (z), unit footprint in x/y."""
        zs = [z for _, z in stack]
        return ((0.0, 0.0, min(zs)), (1.0, 1.0, max(zs)))

    def rib(self, wire: Any, *, thickness: float, depth: float) -> Any:
        # Straight-ribbon volume model: length x thickness x depth. thickness is applied
        # symmetrically about the curve (via the real kernel's trace); depth grows one way.
        # Curve-corner overlap is ignored (consistent with the fake sweep/loft style).
        volume = wire.length * thickness * depth
        return _FakeCombined(volume, self._rib_bounds(wire, thickness, depth))

    def _rib_bounds(self, wire: Any, thickness: float, depth: float) -> Bounds:
        """A coarse envelope: the wire's 2D extent grown by thickness/2 and depth."""
        pts = [p for e in wire.edges for p in e.get("points", [])] or [(0.0, 0.0)]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        half = thickness / 2.0
        return ((min(xs) - half, min(ys) - half, 0.0),
                (max(xs) + half, max(ys) + half, depth))

    def helix_path(self, pitch: float, height: float, radius: float, *,
                   axis_point: Point3, axis_dir: Point3, lefthand: bool = False,
                   cone_angle: float = 0.0) -> Any:
        # Analytic helix length: each turn is sqrt(circumference^2 + pitch^2); the number of
        # turns is height/pitch. cone_angle/lefthand do not affect the length model here.
        turns = height / pitch
        wire = _FakeWire([], "XY")
        wire.length = turns * math.sqrt((2.0 * math.pi * radius) ** 2 + pitch ** 2)
        return wire

    def _face_area(self, face: Any) -> float:
        """Area of a fake face (polygon or wire-face)."""
        if isinstance(face, _FakeWireFace):
            return face.area
        return _polygon_area(face.points)

    def _sweep_bounds(self, path: Any) -> Bounds:
        """A coarse envelope for a swept solid (the path's own 2D extent)."""
        pts = [p for e in path.edges for p in e.get("points", [])] or [(0.0, 0.0)]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        return ((min(xs), min(ys), 0.0), (max(xs), max(ys), 0.0))

    def project_edges(self, edges: list, plane: str, offset: float = 0.0) -> list:
        # FakeKernel edges in tests are already 2D descriptors; identity projection. The
        # fake projection is offset-agnostic (it does not model the plane's world placement).
        return list(edges)

    def extrude(self, face: Any, distance: float | None = None, *,
                symmetric: bool = False, second_distance: float | None = None,
                draft: float = 0.0, thin: float | None = None,
                until: str | None = None, target: Any = None) -> Any:
        # Effective +Z height carries the end-condition analytically: blind/symmetric use
        # `distance` (symmetric only re-centers, so total height is unchanged); two_side
        # sums both sides; until/target take the target's bbox height. draft is ignored in
        # the analytic model (it barely changes volume and the fake has no side walls);
        # thin keeps only a rim of the profile.
        height = self._effective_height(distance, second_distance, until, target)
        wall_area = self._wall_area(face, thin) if thin is not None else None
        return _FakeSolid(face, height, wall_area)

    def revolve(self, face: Any, axis_point: Point3, axis_dir: Point3, *,
                angle: float = 360.0, symmetric: bool = False,
                thin: float | None = None) -> Any:
        # Pappus's theorem: a planar region revolved about an external axis sweeps a volume
        # equal to its area times the distance its centroid travels (area * 2pi * r_c *
        # angle/360). Enough for the fake kernel's volume assertions without modeling the
        # B-rep. `symmetric` only re-centers the arc, so it does not change the volume;
        # `thin` revolves a ring (the wall area).
        pts = getattr(face, "points", None)
        if pts is None:
            raise KernelOpError("revolve needs a polygonal profile in the fake kernel")
        area = self._wall_area(face, thin) if thin is not None else _polygon_area(pts)
        cx, cy = _polygon_centroid(pts)
        r_centroid = _distance_point_to_axis((cx, cy, 0.0), axis_point, axis_dir)
        volume = area * 2.0 * math.pi * r_centroid * (angle / 360.0)
        return _FakeCombined(volume, self._revolve_bounds(pts, r_centroid))

    def _revolve_bounds(self, pts: list, r_centroid: float) -> Bounds:
        # A coarse envelope: the revolved profile reaches at most r_centroid plus its own
        # radial extent from the axis. Sufficient for downstream bbox-based ops in tests.
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        reach = r_centroid + (max(xs) - min(xs))
        return ((-reach, min(ys), -reach), (reach, max(ys), reach))

    def _effective_height(self, distance: float | None, second_distance: float | None,
                          until: str | None, target: Any) -> float:
        if until is not None or target is not None:
            if target is None:
                raise KernelOpError("until extrude needs a target in the fake kernel")
            (_, _, zmin), (_, _, zmax) = self.bounding_box(target)
            return abs(zmax - zmin)
        base = float(distance) if distance is not None else 0.0
        if second_distance is not None:
            base += float(second_distance)
        return base

    def _wall_area(self, face: Any, thin: float) -> float:
        # Outer profile area minus a uniform `thin` inset (a rectangular-bbox model, enough
        # for the volume assertion): a ring of width `thin` around the profile.
        pts = getattr(face, "points", None)
        if pts is None:
            raise KernelOpError("thin wall needs a polygonal profile in the fake kernel")
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        inner = max(0.0, w - 2 * thin) * max(0.0, h - 2 * thin)
        return w * h - inner

    def circle_face(self, center: Point2, diameter: float, plane: str,
                    offset: float = 0.0) -> Any:
        cx, cy = center
        r = diameter / 2.0
        pts = [(cx + r * math.cos(2 * math.pi * i / 48), cy + r * math.sin(2 * math.pi * i / 48))
               for i in range(48)]
        return _FakeFace(pts, plane, offset)

    def cylinder(self, center: Point3, axis: str, diameter: float, length: float) -> Any:
        return _FakeCylinder(center, axis, diameter, length)

    def cone(self, center: Point3, axis: str, bottom_diameter: float,
             top_diameter: float, length: float) -> Any:
        return _FakeCone(center, axis, bottom_diameter, top_diameter, length)

    def cut(self, solid: Any, tools: list) -> Any:
        # Cutting keeps the outer bounds of the solid being drilled/pocketed.
        return _FakeCombined(self.volume(solid) - sum(self.volume(t) for t in tools),
                             self.bounding_box(solid))

    def fuse(self, solids: list) -> Any:
        return _FakeCombined(sum(self.volume(s) for s in solids),
                             self._union_bounds(solids))

    def intersect(self, solids: list) -> Any:
        return _FakeCombined(min(self.volume(s) for s in solids),
                             self.bounding_box(solids[0]))

    def fillet_edges(self, solid: Any, edges: list, radius: float) -> Any:
        return _FakeCombined(self.volume(solid) - radius * len(edges),
                             self.bounding_box(solid))

    def chamfer_edges(self, solid: Any, edges: list, distance: float, *,
                      distance2: float | None = None,
                      angle: float | None = None) -> Any:
        # Analytic volume-delta model. Two-distance uses the mean setback; distance-angle
        # uses the first setback (the angle only reshapes the cut, it does not drive the
        # removed volume in this rough deterministic model).
        if distance2 is not None:
            setback = (distance + distance2) / 2.0
        else:
            setback = distance
        return _FakeCombined(self.volume(solid) - setback * len(edges),
                             self.bounding_box(solid))

    def shell(self, solid: Any, thickness: float, openings: list | None = None) -> Any:
        # Analytic wall-shell volume: outer bbox minus the inner cavity, where the inner box
        # is the outer shrunk by 2*thickness per axis (clamped at 0). Openings do not change
        # the fake volume (a rough delta, consistent with the other fake dress-up models).
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        dx, dy, dz = maxx - minx, maxy - miny, maxz - minz
        outer = dx * dy * dz
        t2 = 2.0 * thickness
        inner = max(dx - t2, 0.0) * max(dy - t2, 0.0) * max(dz - t2, 0.0)
        return _FakeCombined(outer - inner, self.bounding_box(solid))

    def draft(self, solid: Any, faces: list, *, angle: float, neutral: str,
              neutral_offset: float = 0.0) -> Any:
        # Draft only slightly changes volume; model it as a small deterministic delta
        # proportional to sin(angle) and the number of drafted faces. neutral/neutral_offset
        # do not change the fake volume. Deterministic, angle-monotonic, positive.
        factor = 1.0 - math.sin(math.radians(angle)) * 0.01 * len(faces)
        volume = max(self.volume(solid) * factor, 1e-9)
        return _FakeCombined(volume, self.bounding_box(solid))

    def wrap(self, solid: Any, face: Any, *, text: str | None = None,
             profile: Any = None, font_size: float = 5.0, font: str = "Arial",
             font_style: str = "regular", depth: float = 1.0, mode: str = "emboss",
             offset: Point2 = (0.0, 0.0), rotation: float = 0.0) -> Any:
        # Nominal-area model: text stands in as font_size^2 * len(text); a profile uses its
        # face area. emboss adds nominal_area*depth, engrave subtracts it. Mode-signed and
        # deterministic; the real kernel does the true text/extrude/boolean. Clamp > 0.
        if text is not None:
            nominal_area = font_size * font_size * max(len(text), 1)
        else:
            nominal_area = self._face_area(profile)
        delta = nominal_area * depth
        signed = delta if mode == "emboss" else -delta
        volume = max(self.volume(solid) + signed, 1e-9)
        return _FakeCombined(volume, self.bounding_box(solid))

    def _union_bounds(self, solids: list) -> Bounds:
        """The bounding box enclosing all ``solids``."""
        boxes = [self.bounding_box(s) for s in solids]
        lows = [b[0] for b in boxes]
        highs = [b[1] for b in boxes]
        return (
            (min(p[0] for p in lows), min(p[1] for p in lows), min(p[2] for p in lows)),
            (max(p[0] for p in highs), max(p[1] for p in highs), max(p[2] for p in highs)),
        )

    def edges_of(self, solid: Any) -> list:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        infos = []
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "vertical",
                          "mid_z": (minz + maxz) / 2})
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "horizontal", "mid_z": maxz})
        for _ in range(4):
            infos.append({"edge": object(), "orientation": "horizontal", "mid_z": minz})
        return infos

    def describe_elements(self, solid: Any) -> list:
        # Per body, tagging each descriptor with its body_id (single shape = "body/0").
        described: list = []
        for body in self.bodies(solid):
            for descriptor in self._describe_one(body.shape):
                descriptor["body_id"] = body.id
                described.append(descriptor)
        return described

    def _describe_one(self, solid: Any) -> list:
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        faces = [
            _box_face((minx + maxx) / 2, (miny + maxy) / 2, maxz, (0.0, 0.0, 1.0),
                      (maxx - minx) * (maxy - miny), maxz),
            _box_face((minx + maxx) / 2, (miny + maxy) / 2, minz, (0.0, 0.0, -1.0),
                      (maxx - minx) * (maxy - miny), minz),
            _box_face((minx + maxx) / 2, miny, (minz + maxz) / 2, (0.0, -1.0, 0.0),
                      (maxx - minx) * (maxz - minz), (minz + maxz) / 2),
            _box_face((minx + maxx) / 2, maxy, (minz + maxz) / 2, (0.0, 1.0, 0.0),
                      (maxx - minx) * (maxz - minz), (minz + maxz) / 2),
            _box_face(minx, (miny + maxy) / 2, (minz + maxz) / 2, (-1.0, 0.0, 0.0),
                      (maxy - miny) * (maxz - minz), (minz + maxz) / 2),
            _box_face(maxx, (miny + maxy) / 2, (minz + maxz) / 2, (1.0, 0.0, 0.0),
                      (maxy - miny) * (maxz - minz), (minz + maxz) / 2),
        ]
        edges = []
        for info in self.edges_of(solid):
            edges.append({
                "kind": "edge", "handle": info["edge"], "geom_type": "line",
                "length": 0.0, "center": (0.0, 0.0, info["mid_z"]),
                "orientation": info["orientation"],
                "min_z": info["mid_z"], "mid_z": info["mid_z"], "max_z": info["mid_z"],
            })
        return faces + edges

    def version(self) -> str:
        return "fake-1"

    def signature(self, solid: Any) -> dict:
        if isinstance(solid, BodySet):
            # Per-body signatures ordered by a deterministic key (id, volume, bbox), so the
            # multibody signature is independent of body order. Single-body path unchanged.
            per_body = [(b.id, self.signature(b.shape)) for b in solid.bodies]
            per_body.sort(key=lambda p: (p[0], p[1]["volume"], p[1]["bbox"]))
            return {"bodies": [sig for _, sig in per_body]}
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(solid)
        dx, dy, dz = maxx - minx, maxy - miny, maxz - minz
        area = 2.0 * (dx * dy + dy * dz + dx * dz)
        return {
            "counts": {"face": 6, "edge": 12, "vertex": 8},
            "surface_types": {"plane": 6},
            "curve_types": {"line": 12},
            "volume": self.volume(solid),
            "area": area,
            "bbox": ((minx, miny, minz), (maxx, maxy, maxz)),
            "cog": ((minx + maxx) / 2, (miny + maxy) / 2, (minz + maxz) / 2),
        }

    def bodies(self, shape: Any) -> list:
        # A BodySet exposes its bodies; any other shape is a single implicit solid body.
        if isinstance(shape, BodySet):
            return shape.bodies
        return [Body(id="body/0", kind="solid", shape=shape, created_by="")]

    def union_bodies(self, shapes: list, *, origin: str) -> Any:
        return union_bodies(shapes, origin)

    def transform(self, shape: Any, *, move: Point3 = (0.0, 0.0, 0.0),
                  rotate: dict | None = None, scale: Any = None) -> Any:
        # Analytic: move/rotate preserve volume; uniform scale k**3; non-uniform sx*sy*sz.
        # Bounds are scaled then shifted (a coarse axis-aligned envelope; rotation is not
        # applied to the fake bbox). Exact enough for volume/signature tests.
        volume = self.volume(shape)
        (minx, miny, minz), (maxx, maxy, maxz) = self.bounding_box(shape)
        if scale is not None:
            if isinstance(scale, (int, float)):
                sx = sy = sz = float(scale)
            else:
                sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
            volume *= abs(sx * sy * sz)
            minx, maxx = minx * sx, maxx * sx
            miny, maxy = miny * sy, maxy * sy
            minz, maxz = minz * sz, maxz * sz
        dx, dy, dz = float(move[0]), float(move[1]), float(move[2])
        bounds = ((min(minx, maxx) + dx, min(miny, maxy) + dy, min(minz, maxz) + dz),
                  (max(minx, maxx) + dx, max(miny, maxy) + dy, max(minz, maxz) + dz))
        return _FakeCombined(volume, bounds)

    def volume(self, solid: Any) -> float:
        if isinstance(solid, BodySet):
            return sum(self.volume(b.shape) for b in solid.bodies)
        if isinstance(solid, (_FakeCylinder, _FakeCone, _FakeCombined)):
            return solid.volume_val
        if getattr(solid, "wall_area", None) is not None:
            return solid.wall_area * solid.distance
        if isinstance(solid.face, _FakeWireFace):
            return solid.face.area * solid.distance
        return _polygon_area(solid.face.points) * solid.distance

    def bounding_box(self, solid: Any) -> Bounds:
        if isinstance(solid, BodySet):
            boxes = [self.bounding_box(b.shape) for b in solid.bodies]
            lows = [b[0] for b in boxes]
            highs = [b[1] for b in boxes]
            return ((min(x for x, _, _ in lows), min(y for _, y, _ in lows),
                     min(z for _, _, z in lows)),
                    (max(x for x, _, _ in highs), max(y for _, y, _ in highs),
                     max(z for _, _, z in highs)))
        if isinstance(solid, _FakeCombined):
            return solid.bounds
        xs = [x for x, _ in solid.face.points]
        ys = [y for _, y in solid.face.points]
        # Bucket 0.1 uses the XY plane; extrude along +Z by distance.
        return ((min(xs), min(ys), 0.0), (max(xs), max(ys), solid.distance))

    def export(self, solid: Any, path: str) -> None:
        raise NotImplementedError("FakeKernel does not export geometry")


def _box_face(cx: float, cy: float, cz: float, normal: Point3, area: float,
              z: float) -> dict:
    """A synthetic planar face descriptor for the FakeKernel's axis-aligned bounds."""
    return {
        "kind": "face", "handle": object(), "geom_type": "planar", "normal": normal,
        "area": area, "center": (cx, cy, cz), "min_z": z, "mid_z": z, "max_z": z,
    }


def _wire_length(edges: list) -> float:
    """Summed length of ordered edge descriptors (an arc approximated by its 3 points)."""
    total = 0.0
    for edge in edges:
        pts = edge.get("points", [])
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            total += math.hypot(x1 - x0, y1 - y0)
    return total


def _prismatoid_volume(stack: list[tuple[float, float]]) -> float:
    """Trapezoidal volume through (area, offset) sections ordered along the stack axis."""
    total = 0.0
    for i in range(len(stack) - 1):
        (a0, z0), (a1, z1) = stack[i], stack[i + 1]
        total += (a0 + a1) / 2.0 * abs(z1 - z0)
    return total


def _polygon_area(points: list[Point2]) -> float:
    """Shoelace area of a closed ring given as non-repeating vertices."""
    n = len(points)
    total = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def _polygon_centroid(points: list[Point2]) -> Point2:
    """Area centroid of a closed polygon ring (non-repeating vertices)."""
    n = len(points)
    a = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-12:
        return points[0]
    return (cx / (6.0 * a), cy / (6.0 * a))


def _distance_point_to_axis(point: Point3, axis_point: Point3, axis_dir: Point3) -> float:
    """Perpendicular distance from ``point`` to the line (``axis_point``, unit ``axis_dir``)."""
    px, py, pz = point
    ax, ay, az = axis_point
    dx, dy, dz = axis_dir
    wx, wy, wz = px - ax, py - ay, pz - az
    # |cross(w, dir)| / |dir|; dir is unit, so just the cross-product magnitude.
    cx = wy * dz - wz * dy
    cy = wz * dx - wx * dz
    cz = wx * dy - wy * dx
    return math.sqrt(cx * cx + cy * cy + cz * cz)


def _wire_ring(edges: list) -> list[Point2]:
    """Ordered endpoint ring for a wire's bounds (circle -> its bbox corners).

    A spline/bezier contributes all its defining points so the bbox spans the control
    polygon, not just the chord endpoints.
    """
    if len(edges) == 1 and edges[0]["kind"] == "circle":
        cx, cy = edges[0]["center"]
        r = edges[0]["radius"]
        return [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    ring: list[Point2] = []
    for edge in edges:
        if edge["kind"] in ("bezier", "spline"):
            ring.extend(edge["points"])
        else:
            ring.append(edge["points"][0])
    return ring


def _wire_face_area(edges: list) -> float:
    """Area of a closed wire loop; arcs are tessellated so the bulge sign is correct."""
    if len(edges) == 1 and edges[0]["kind"] == "circle":
        return math.pi * edges[0]["radius"] ** 2
    dense: list[Point2] = []
    for edge in edges:
        if edge["kind"] == "arc":
            dense.extend(_arc_samples(edge["points"], 24)[:-1])
        elif edge["kind"] in ("bezier", "spline"):
            # Defining-polygon approximation: the fake kernel does not evaluate the true
            # curve, so a spline's contribution to the loop area is its control/through
            # points. Deterministic and non-zero for a bulging curve; exact area is the
            # real kernel's job.
            dense.extend(edge["points"][:-1])
        else:
            dense.append(edge["points"][0])
    return _polygon_area(dense)


def _arc_samples(points: list, n: int) -> list[Point2]:
    """Sample an arc (start, mid, end) into ``n`` points inclusive of both ends."""
    (sx, sy), (mx, my), (ex, ey) = points
    center = _circumcenter((sx, sy), (mx, my), (ex, ey))
    if center is None:
        return [(sx, sy), (ex, ey)]
    cx, cy = center
    r = math.hypot(sx - cx, sy - cy)
    a0 = math.atan2(sy - cy, sx - cx)
    am = math.atan2(my - cy, mx - cx)
    a1 = math.atan2(ey - cy, ex - cx)
    # unwrap so the sweep passes through the mid angle
    am_u = _unwrap(a0, am)
    a1_u = _unwrap(am_u, a1)
    return [(cx + r * math.cos(a0 + (a1_u - a0) * i / (n - 1)),
             cy + r * math.sin(a0 + (a1_u - a0) * i / (n - 1))) for i in range(n)]


def _unwrap(reference: float, angle: float) -> float:
    """Shift ``angle`` by multiples of 2pi to lie within pi of ``reference``."""
    while angle - reference > math.pi:
        angle -= 2.0 * math.pi
    while angle - reference < -math.pi:
        angle += 2.0 * math.pi
    return angle


def _circumcenter(a: Point2, b: Point2, c: Point2) -> Point2 | None:
    """Circumcircle center of a,b,c; None for (near-)collinear points."""
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    return (ux, uy)
