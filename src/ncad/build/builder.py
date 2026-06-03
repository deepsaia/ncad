"""Pure builder: turns a spec into geometry via an injected Kernel.

``build(spec)`` has no randomness and no global state, so the same spec always yields
identical geometry (design.md §3). Walls are extruded boxes from their centerlines,
unioned for the visual solid; openings are boolean-subtracted; a floor slab and a
registry-dispatched roof complete the model. v1 assumes axis-aligned walls.
"""

import logging
import math

from ncad.build.roof_builders import ROOF_BUILDERS
from ncad.kernel.kernel import Kernel

logger = logging.getLogger(__name__)

_AXIS_TOLERANCE = 1e-9
# Extra depth on opening cut boxes so the boolean fully passes through the wall faces.
_CUT_OVERSHOOT = 0.01
_SLAB_THICKNESS = 0.2
# Balcony proportions (meters): a thin floor slab + a waist-high railing of slim rods.
_BALCONY_SLAB_THICKNESS = 0.15
_RAILING_HEIGHT = 1.0
_ROD_SIZE = 0.04
_ROD_SPACING = 0.15


class Builder:
    """Builds geometry from a spec using a swappable geometry kernel."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: The geometry backend to build with."""
        self._kernel = kernel

    def build(self, spec: dict):
        """Build the full model solid for ``spec``.

        :param spec: A schema-valid building spec dict.
        :return: An opaque solid handle from the kernel.
        :raises ValueError: If the roof kind is unknown.
        """
        storeys = spec["storeys"]
        top_index = len(storeys) - 1

        storey_solids = []
        for index, storey in enumerate(storeys):
            # Only the top storey carries the building roof; intermediate storeys get a
            # flat ceiling slab (the floor of the storey above).
            roof = spec["roof"] if index == top_index else None
            storey_solids.append(self._build_storey(storey, roof))

        # Single storey reduces to exactly today's geometry (one storey solid → returned
        # as-is), keeping existing buildings byte-identical.
        solid = storey_solids[0]
        if len(storey_solids) > 1:
            solid = self._kernel.union(storey_solids)

        logger.debug(
            "built model: storeys=%d volume=%.3f", len(storeys), self._kernel.volume(solid)
        )
        return solid

    def _build_storey(self, storey: dict, roof: dict | None):
        """Build one storey's solid: floor slab + walls, plus a roof (top) or ceiling.

        ``roof`` is the building roof dict for the top storey, or None for intermediate
        storeys (which get a flat ceiling slab instead). The single-storey, roof-bearing
        case emits exactly the original two-step union, so existing geometry is unchanged.
        """
        elevation = storey["elevation"]
        storey_height = storey["height"]
        footprint = storey.get("footprint")
        top_z = elevation + storey_height

        wall_solids = [
            self._build_wall(wall, elevation, storey_height) for wall in storey["walls"]
        ]
        if footprint is not None:
            floor = self._build_polygon_slab(footprint, top_z=elevation, thickness=_SLAB_THICKNESS)
            cap = self._build_polygon_roof(roof, footprint, top_z=top_z) if roof is not None \
                else self._build_polygon_slab(footprint, top_z=top_z, thickness=_SLAB_THICKNESS)
        else:
            bounds = self._footprint_bounds(storey["walls"])
            floor = self._build_slab(bounds, top_z=elevation, thickness=_SLAB_THICKNESS)
            cap = self._build_roof(roof, bounds, top_z=top_z) if roof is not None \
                else self._build_slab(bounds, top_z=top_z, thickness=_SLAB_THICKNESS)

        solid = self._kernel.union([floor, *wall_solids])
        solid = self._kernel.union([solid, cap])

        balcony_solids = self._build_balconies(storey, elevation, storey_height)
        if balcony_solids:
            solid = self._kernel.union([solid, *balcony_solids])
        return solid

    def _build_balconies(self, storey: dict, elevation: float, storey_height: float) -> list:
        """Build a solid for each balcony on this storey (empty if none)."""
        walls_by_id = {wall["id"]: wall for wall in storey["walls"]}
        solids = []
        for balcony in storey.get("balconies", []):
            wall = walls_by_id.get(balcony["wall_id"])
            if wall is not None:
                solids.append(self._build_balcony(wall, balcony, elevation, storey_height))
        return solids

    def _build_balcony(self, wall: dict, balcony: dict, elevation: float, storey_height: float):
        """A cantilevered balcony: floor slab + perimeter railing (vertical rods, side
        fences, top rail) built from thin boxes, projecting out from the wall's exterior.
        """
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        wx, wy = x1 - x0, y1 - y0
        wlen = math.hypot(wx, wy) or 1.0
        ux, uy = wx / wlen, wy / wlen          # along-wall unit
        nx, ny = wy / wlen, -wx / wlen          # outward normal (exterior side, -y for south wall)
        length = balcony["length"]
        depth = balcony["depth"]
        center_t = balcony["along"] * wlen
        # Center of the balcony slab: at the wall, pushed out by depth/2.
        cx = x0 + ux * center_t + nx * (depth / 2)
        cy = y0 + uy * center_t + ny * (depth / 2)

        pieces = [self._balcony_slab(cx, cy, ux, uy, nx, ny, length, depth, elevation)]
        pieces.extend(
            self._balcony_railing(x0, y0, ux, uy, nx, ny, center_t, length, depth, elevation)
        )
        return self._kernel.union(pieces)

    def _balcony_slab(self, cx, cy, ux, uy, nx, ny, length, depth, elevation):
        """The cantilevered floor slab, modelled as a polygon prism flush with the floor."""
        hl, hd = length / 2, depth / 2
        corners = [
            (cx - ux * hl - nx * hd, cy - uy * hl - ny * hd),
            (cx + ux * hl - nx * hd, cy + uy * hl - ny * hd),
            (cx + ux * hl + nx * hd, cy + uy * hl + ny * hd),
            (cx - ux * hl + nx * hd, cy - uy * hl + ny * hd),
        ]
        return self._kernel.extrude_polygon(
            corners, base_z=elevation - _BALCONY_SLAB_THICKNESS, height=_BALCONY_SLAB_THICKNESS
        )

    def _balcony_railing(self, x0, y0, ux, uy, nx, ny, center_t, length, depth, elevation):
        """Vertical rods around the outer + side edges, plus a top rail tying them."""
        pieces = []
        # Outer edge runs parallel to the wall at distance `depth`; the two side edges run
        # outward at the balcony ends. Place rods along all three, then a top rail.
        start_t = center_t - length / 2
        # Outer-edge rod line endpoints (at the far edge).
        ax = x0 + ux * start_t + nx * depth
        ay = y0 + uy * start_t + ny * depth
        bx = ax + ux * length
        by = ay + uy * length
        pieces.extend(self._rod_line((ax, ay), (bx, by), elevation))
        # Two side edges: from the wall out to the outer corners.
        wax, way = x0 + ux * start_t, y0 + uy * start_t
        wbx, wby = wax + ux * length, way + uy * length
        pieces.extend(self._rod_line((wax, way), (ax, ay), elevation))
        pieces.extend(self._rod_line((wbx, wby), (bx, by), elevation))
        # Top rail capping every railed edge: the outer edge AND both sides.
        rail_z = elevation + _RAILING_HEIGHT
        pieces.append(self._rail_box((ax, ay), (bx, by), rail_z))      # outer edge
        pieces.append(self._rail_box((wax, way), (ax, ay), rail_z))    # left side
        pieces.append(self._rail_box((wbx, wby), (bx, by), rail_z))    # right side
        return pieces

    def _rod_line(self, start, end, elevation):
        """A row of thin vertical rod boxes spaced along a segment."""
        (sx, sy), (ex, ey) = start, end
        seg = math.hypot(ex - sx, ey - sy)
        count = max(2, int(seg / _ROD_SPACING))
        rods = []
        for i in range(count + 1):
            t = i / count
            px, py = sx + (ex - sx) * t, sy + (ey - sy) * t
            rods.append(
                self._kernel.box(
                    center=(px, py, elevation + _RAILING_HEIGHT / 2),
                    size=(_ROD_SIZE, _ROD_SIZE, _RAILING_HEIGHT),
                )
            )
        return rods

    def _rail_box(self, start, end, z):
        """A thin horizontal top-rail bar from start to end at height z."""
        (sx, sy), (ex, ey) = start, end
        length = math.hypot(ex - sx, ey - sy)
        dx, dy = (ex - sx) / (length or 1.0), (ey - sy) / (length or 1.0)
        # A thin oriented bar along the rail direction (perpendicular offset for width).
        half = _ROD_SIZE
        nx, ny = -dy, dx
        corners = [
            (sx - nx * half, sy - ny * half),
            (ex - nx * half, ey - ny * half),
            (ex + nx * half, ey + ny * half),
            (sx + nx * half, sy + ny * half),
        ]
        return self._kernel.extrude_polygon(corners, base_z=z - _ROD_SIZE, height=_ROD_SIZE * 2)

    def _build_polygon_slab(self, footprint: list, top_z: float, thickness: float):
        """Slab following an arbitrary footprint polygon (rounded corners if present)."""
        return self._extrude_footprint(footprint, base_z=top_z - thickness, height=thickness)

    def _build_polygon_roof(self, roof: dict, footprint: list, top_z: float):
        """Roof over a footprint polygon: flat follows the outline; pitched roofs are
        allowed only over a rectangular footprint (routed to the roof registry via its
        bounding box). Pitched over non-rectangular footprints needs a straight skeleton
        and stays deferred.
        """
        kind = roof["kind"]
        if kind == "flat":
            thickness = roof.get("thickness", _SLAB_THICKNESS)
            return self._extrude_footprint(footprint, base_z=top_z, height=thickness)

        bounds = _footprint_rectangle_bounds(footprint)
        if bounds is None:
            raise ValueError(
                f"roof kind {kind!r} is only supported over a rectangular footprint; "
                "pitched roofs over L/T/U/irregular shapes need a straight skeleton "
                "(use 'flat' for non-rectangular footprints; dome is a future slice)"
            )
        return self._build_roof(roof, bounds, top_z)

    def _extrude_footprint(self, footprint: list, base_z: float, height: float):
        """Extrude a footprint, rounding any corners that carry a positive corner_radius."""
        polygon, corner_radii = _parse_footprint(footprint)
        if corner_radii:
            return self._kernel.extrude_rounded_polygon(polygon, corner_radii, base_z, height)
        return self._kernel.extrude_polygon(polygon, base_z, height)

    def _build_wall(self, wall: dict, elevation: float, storey_height: float):
        """One wall: arc band, axis-aligned box (with openings), or oriented rectangle."""
        height = wall.get("height") or storey_height
        thickness = wall["thickness"]
        if "arc" in wall:
            return self._build_arc_wall(wall, elevation, height, thickness)
        if not _is_axis_aligned(wall):
            return self._build_oriented_wall(wall, elevation, height, thickness)

        center, size = self._wall_box(wall, elevation, height, thickness)
        solid = self._kernel.box(center=center, size=size)
        cuts = [
            self._opening_box(wall, opening, elevation, thickness)
            for opening in wall.get("openings", [])
        ]
        if cuts:
            solid = self._kernel.subtract(solid, cuts)
        return solid

    def _build_oriented_wall(self, wall: dict, elevation: float, height: float, thickness: float):
        """A straight wall at any angle: a thin rectangle extruded up (no openings in v1)."""
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        # Unit normal to the wall direction, scaled to half-thickness.
        nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
        rectangle = [
            (x0 + nx, y0 + ny),
            (x1 + nx, y1 + ny),
            (x1 - nx, y1 - ny),
            (x0 - nx, y0 - ny),
        ]
        return self._kernel.extrude_polygon(rectangle, base_z=elevation, height=height)

    def _build_arc_wall(self, wall: dict, elevation: float, height: float, thickness: float):
        """A curved wall turning a rounded corner (no openings in v1 — corner arcs)."""
        center = wall["arc"]["center"]
        (sx, sy), (ex, ey) = wall["start"], wall["end"]
        radius = math.hypot(sx - center[0], sy - center[1])
        start_angle = math.degrees(math.atan2(sy - center[1], sx - center[0]))
        end_angle = math.degrees(math.atan2(ey - center[1], ex - center[0]))
        # The arc band always spans the minor arc between the two tangent points, so the
        # endpoint order (and the clockwise flag) doesn't change the swept region.
        return self._kernel.arc_wall(
            center=(center[0], center[1]),
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            base_z=elevation,
            height=height,
            thickness=thickness,
        )

    def _wall_box(self, wall: dict, elevation: float, height: float, thickness: float):
        """Center and size of an axis-aligned wall box."""
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        cz = elevation + height / 2
        if abs(y1 - y0) < _AXIS_TOLERANCE:  # horizontal wall (runs along x)
            size = (abs(x1 - x0), thickness, height)
        elif abs(x1 - x0) < _AXIS_TOLERANCE:  # vertical wall (runs along y)
            size = (thickness, abs(y1 - y0), height)
        else:
            raise ValueError(
                f"wall {wall['id']!r} is not axis-aligned; v1 supports axis-aligned walls only"
            )
        return (cx, cy, cz), size

    def _opening_box(self, wall: dict, opening: dict, elevation: float, thickness: float):
        """Subtraction box for an opening, positioned along the wall centerline."""
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        along = opening["along"]
        px, py = x0 + (x1 - x0) * along, y0 + (y1 - y0) * along
        width, height, sill = opening["width"], opening["height"], opening.get("sill", 0.0)
        cz = elevation + sill + height / 2
        depth = thickness + _CUT_OVERSHOOT
        if abs(y1 - y0) < _AXIS_TOLERANCE:  # horizontal wall
            size = (width, depth, height)
        else:  # vertical wall
            size = (depth, width, height)
        return self._kernel.box(center=(px, py, cz), size=size)

    def _build_slab(self, bounds: tuple, top_z: float, thickness: float):
        """A slab covering the footprint, with its top at ``top_z``."""
        (minx, miny), (maxx, maxy) = bounds
        center = ((minx + maxx) / 2, (miny + maxy) / 2, top_z - thickness / 2)
        size = (maxx - minx, maxy - miny, thickness)
        return self._kernel.box(center=center, size=size)

    def _build_roof(self, roof: dict, bounds: tuple, top_z: float):
        kind = roof["kind"]
        builder = ROOF_BUILDERS.get(kind)
        if builder is None:
            raise ValueError(f"unknown roof kind {kind!r}; known: {sorted(ROOF_BUILDERS)}")
        return builder(self._kernel, roof, bounds, top_z)

    def _footprint_bounds(self, walls: list[dict]) -> tuple:
        """Bounding rectangle of all wall endpoints, as ((minx,miny),(maxx,maxy))."""
        xs = [p for wall in walls for p in (wall["start"][0], wall["end"][0])]
        ys = [p for wall in walls for p in (wall["start"][1], wall["end"][1])]
        return (min(xs), min(ys)), (max(xs), max(ys))


def _footprint_rectangle_bounds(footprint: list):
    """``((minx,miny),(maxx,maxy))`` if the footprint is a plain axis-aligned rectangle,
    else None. Rounded (object) vertices or non-rectangular outlines return None.
    """
    if len(footprint) != 4 or any(isinstance(v, dict) for v in footprint):
        return None
    xs = sorted({round(v[0], 6) for v in footprint})
    ys = sorted({round(v[1], 6) for v in footprint})
    if len(xs) != 2 or len(ys) != 2:
        return None
    return (xs[0], ys[0]), (xs[1], ys[1])


def _is_axis_aligned(wall: dict) -> bool:
    """True if the wall runs along x or y (so the box + opening path applies)."""
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return abs(y1 - y0) < _AXIS_TOLERANCE or abs(x1 - x0) < _AXIS_TOLERANCE


def _parse_footprint(footprint: list) -> tuple:
    """Split a footprint into a plain (x, y) polygon plus a {index: radius} corner map.

    A vertex is either a plain ``[x, y]`` or an object ``{"point": [x, y],
    "corner_radius": r}``; only positive radii populate the map.
    """
    polygon = []
    corner_radii = {}
    for index, vertex in enumerate(footprint):
        if isinstance(vertex, dict):
            point = vertex["point"]
            radius = vertex.get("corner_radius", 0.0)
            if radius > 0:
                corner_radii[index] = radius
        else:
            point = vertex
        polygon.append((point[0], point[1]))
    return polygon, corner_radii
