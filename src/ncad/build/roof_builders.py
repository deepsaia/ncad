"""Roof geometry builders, dispatched by roof kind via a registry.

Adding a roof type is a new function plus a registry entry — not a new branch scattered
through the builder (design.md §3). v1 ships ``flat`` only.
"""

from typing import Any, Callable

from ncad.kernel.kernel import Kernel

# A roof builder takes (kernel, roof_spec, footprint_bounds, top_z) and returns a solid.
# footprint_bounds is ((minx, miny), (maxx, maxy)); top_z is the wall-top elevation.
RoofBuilder = Callable[[Kernel, dict, tuple, float], Any]


def build_flat_roof(kernel: Kernel, roof: dict, footprint_bounds: tuple, top_z: float) -> Any:
    """A flat slab covering the footprint, sitting on top of the walls."""
    (minx, miny), (maxx, maxy) = footprint_bounds
    thickness = roof["thickness"]
    center = ((minx + maxx) / 2, (miny + maxy) / 2, top_z + thickness / 2)
    size = (maxx - minx, maxy - miny, thickness)
    return kernel.box(center=center, size=size)


ROOF_BUILDERS: dict[str, RoofBuilder] = {
    "flat": build_flat_roof,
}
