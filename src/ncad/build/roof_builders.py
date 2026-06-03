"""Roof geometry builders, dispatched by roof kind via a registry.

Adding a roof type is a new function plus a registry entry — not a new branch scattered
through the builder (design.md §3). Pitched roofs (shed/gable) use the kernel's prism
primitive; flat uses a box. All roofs sit on top of the walls (base at ``top_z``).
"""

from collections.abc import Callable
from typing import Any

from ncad.kernel.kernel import Kernel

# A roof builder takes (kernel, roof_spec, footprint_bounds, top_z) and returns a solid.
# footprint_bounds is ((minx, miny), (maxx, maxy)); top_z is the wall-top elevation.
RoofBuilder = Callable[[Kernel, dict, tuple, float], Any]

_DEFAULT_ROOF_THICKNESS = 0.2
_DEFAULT_PITCH = 0.4  # rise per unit half-span (gable) or per unit span (shed)


def build_flat_roof(kernel: Kernel, roof: dict, footprint_bounds: tuple, top_z: float) -> Any:
    """A flat slab covering the footprint, sitting on top of the walls."""
    (minx, miny), (maxx, maxy) = footprint_bounds
    thickness = roof.get("thickness", _DEFAULT_ROOF_THICKNESS)
    center = ((minx + maxx) / 2, (miny + maxy) / 2, top_z + thickness / 2)
    size = (maxx - minx, maxy - miny, thickness)
    return kernel.box(center=center, size=size)


def build_gable_roof(kernel: Kernel, roof: dict, footprint_bounds: tuple, top_z: float) -> Any:
    """A gable (two-sided pitched) roof: ridge along the longer axis, triangular ends."""
    (minx, miny), (maxx, maxy) = footprint_bounds
    ridge_axis = _ridge_axis(roof, footprint_bounds)
    pitch = roof.get("pitch", _DEFAULT_PITCH)
    if ridge_axis == "x":  # ridge along x; triangle spans y
        cross_lo, cross_hi, run_lo, run_hi = miny, maxy, minx, maxx
    else:  # ridge along y; triangle spans x
        cross_lo, cross_hi, run_lo, run_hi = minx, maxx, miny, maxy
    rise = pitch * (cross_hi - cross_lo) / 2.0
    mid = (cross_lo + cross_hi) / 2.0
    profile = [(cross_lo, top_z), (cross_hi, top_z), (mid, top_z + rise)]
    return kernel.prism(profile=profile, axis=ridge_axis, start=run_lo, end=run_hi)


def build_shed_roof(kernel: Kernel, roof: dict, footprint_bounds: tuple, top_z: float) -> Any:
    """A shed (mono-pitch) roof: a wedge low on one eave, high on the other."""
    (minx, miny), (maxx, maxy) = footprint_bounds
    ridge_axis = _ridge_axis(roof, footprint_bounds)
    pitch = roof.get("pitch", _DEFAULT_PITCH)
    thickness = roof.get("thickness", _DEFAULT_ROOF_THICKNESS)
    if ridge_axis == "x":  # slope across y
        cross_lo, cross_hi, run_lo, run_hi = miny, maxy, minx, maxx
    else:  # slope across x
        cross_lo, cross_hi, run_lo, run_hi = minx, maxx, miny, maxy
    rise = pitch * (cross_hi - cross_lo)
    # Right-trapezoid: flat base at top_z, top edge sloping from low eave to high eave.
    profile = [
        (cross_lo, top_z),
        (cross_hi, top_z),
        (cross_hi, top_z + thickness + rise),
        (cross_lo, top_z + thickness),
    ]
    return kernel.prism(profile=profile, axis=ridge_axis, start=run_lo, end=run_hi)


def build_hip_roof(kernel: Kernel, roof: dict, footprint_bounds: tuple, top_z: float) -> Any:
    """A hip (four-sided sloped) roof over a rectangle: the intersection of two
    perpendicular gable tents peaking at the same height — every eave slopes inward to a
    central ridge (rectangle) or apex (square).
    """
    (minx, miny), (maxx, maxy) = footprint_bounds
    pitch = roof.get("pitch", _DEFAULT_PITCH)
    rise = pitch * min(maxx - minx, maxy - miny) / 2.0
    midx, midy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    # Tent ridged along x (triangle spans y), peak `rise` above top_z.
    tent_x = kernel.prism(
        profile=[(miny, top_z), (maxy, top_z), (midy, top_z + rise)],
        axis="x", start=minx, end=maxx,
    )
    # Tent ridged along y (triangle spans x), same peak.
    tent_y = kernel.prism(
        profile=[(minx, top_z), (maxx, top_z), (midx, top_z + rise)],
        axis="y", start=miny, end=maxy,
    )
    return kernel.intersect([tent_x, tent_y])


def _ridge_axis(roof: dict, footprint_bounds: tuple) -> str:
    """Ridge/slope direction: explicit ``ridge_axis``, else the footprint's longer axis."""
    explicit = roof.get("ridge_axis")
    if explicit in ("x", "y"):
        return explicit
    (minx, miny), (maxx, maxy) = footprint_bounds
    return "x" if (maxx - minx) >= (maxy - miny) else "y"


ROOF_BUILDERS: dict[str, RoofBuilder] = {
    "flat": build_flat_roof,
    "gable": build_gable_roof,
    "shed": build_shed_roof,
    "hip": build_hip_roof,
}
