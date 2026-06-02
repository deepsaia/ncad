"""Pure builder: turns a spec into geometry via an injected Kernel.

``build(spec)`` has no randomness and no global state, so the same spec always yields
identical geometry (design.md §3). Walls are extruded boxes from their centerlines,
unioned for the visual solid; openings are boolean-subtracted; a floor slab and a
registry-dispatched roof complete the model. v1 assumes axis-aligned walls.
"""

import logging

from ncad.build.roof_builders import ROOF_BUILDERS
from ncad.kernel.kernel import Kernel

logger = logging.getLogger(__name__)

_AXIS_TOLERANCE = 1e-9
# Extra depth on opening cut boxes so the boolean fully passes through the wall faces.
_CUT_OVERSHOOT = 0.01
_SLAB_THICKNESS = 0.2


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
        storey = spec["storeys"][0]
        elevation = storey["elevation"]
        storey_height = storey["height"]

        wall_solids = [
            self._build_wall(wall, elevation, storey_height) for wall in storey["walls"]
        ]
        bounds = self._footprint_bounds(storey["walls"])
        floor = self._build_slab(bounds, top_z=elevation, thickness=_SLAB_THICKNESS)

        solid = self._kernel.union([floor, *wall_solids])

        roof_solid = self._build_roof(spec["roof"], bounds, top_z=elevation + storey_height)
        solid = self._kernel.union([solid, roof_solid])

        logger.debug(
            "built model: walls=%d volume=%.3f", len(wall_solids), self._kernel.volume(solid)
        )
        return solid

    def _build_wall(self, wall: dict, elevation: float, storey_height: float):
        """One wall as a box with its openings subtracted."""
        height = wall.get("height") or storey_height
        thickness = wall["thickness"]
        center, size = self._wall_box(wall, elevation, height, thickness)
        solid = self._kernel.box(center=center, size=size)

        cuts = [
            self._opening_box(wall, opening, elevation, thickness)
            for opening in wall.get("openings", [])
        ]
        if cuts:
            solid = self._kernel.subtract(solid, cuts)
        return solid

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
