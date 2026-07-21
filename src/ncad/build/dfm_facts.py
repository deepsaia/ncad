"""Extract the manufacturability-relevant geometry facts from a part's B-rep. Facts only, no rules.

The honest split for a DFM seam (see the backlog's B10): this reads objective geometry from the
kernel and states nothing about whether the part is manufacturable. The comparison against process
limits lives in ManufacturabilityChecker with an external rule set, so a threshold change never
touches fact extraction. ncad reads these from the real B-rep (better than parsing a mesh):

- ``min_wall_thickness`` (mm): the kernel's conservative wall/thickness floor, or None if unknown.
- ``bbox_size`` (mm): overall (dx, dy, dz), the plate/stock envelope.
- ``holes``: per cylindrical face, its ``diameter`` (mm) and ``axis`` direction - candidate drilled
  or cut holes; a through vs blind distinction is not attempted here (facts only).
- ``smallest_hole_diameter`` (mm): the min hole diameter, or None when the part has no round holes.

One class; the ``extract`` method is pure over the shape (no mutation, no randomness).
"""

from typing import Any

from ncad.kernel.kernel import Kernel


class DfmFacts:
    """Reads manufacturability-relevant facts (thickness, envelope, holes) from a part's B-rep."""

    def __init__(self, kernel: Kernel) -> None:
        self._kernel = kernel

    def extract(self, shape: Any) -> dict:
        """Return the DFM fact record for ``shape`` (see the module docstring for the shape)."""
        (x0, y0, z0), (x1, y1, z1) = self._kernel.bounding_box(shape)
        holes = self._holes(shape)
        diameters = [h["diameter"] for h in holes]
        return {
            "min_wall_thickness": self._kernel.min_wall_thickness(shape),
            "bbox_size": [x1 - x0, y1 - y0, z1 - z0],
            "holes": holes,
            "smallest_hole_diameter": min(diameters) if diameters else None,
        }

    def _holes(self, shape: Any) -> list[dict]:
        """Candidate round holes: one entry per cylindrical face, with diameter + axis direction."""
        holes: list[dict] = []
        for element in self._kernel.describe_elements(shape):
            if element.get("kind") != "face" or "radius" not in element:
                continue
            holes.append({
                "diameter": 2.0 * element["radius"],
                "axis": element.get("axis_direction"),
            })
        return holes
