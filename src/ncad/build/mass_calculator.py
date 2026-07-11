"""Derive mass properties from geometry volume + a body's material density (on demand).

Mass is DERIVED, never stored: ``mass_kg = density_kg_m3 * volume_mm3 * 1e-9`` (geometry is in
mm, so volume is mm^3, and 1 mm^3 = 1e-9 m^3; density is authored in kg/m^3). COG is in mm; the
assembly COG is the mass-weighted mean of per-body COGs. This is a layer OVER the kernel: the
kernel stays geometry-only (volume + signature cog); density comes from the material document.
Iterates bodies individually because the BodySet signature drops per-body cog.
"""

import logging
from typing import Any

from ncad.build.material_error import MaterialError
from ncad.build.material_resolver import MaterialResolver

logger = logging.getLogger(__name__)

_MM3_TO_M3 = 1e-9  # 1 cubic millimetre in cubic metres; converts density*volume to kg


class MassCalculator:
    """Computes per-body and assembly mass properties from volume + material density."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel

    def mass_properties(self, shape: Any, resolver: MaterialResolver) -> dict:
        """Per-body and assembly mass/volume/COG for ``shape`` under ``resolver``'s materials."""
        bodies_out: list[dict] = []
        # Iterate bodies individually: the BodySet signature sorts and drops per-body cog, so
        # each body's own single-shape signature is the reliable source of its cog.
        for body in self._kernel.bodies(shape):
            mat = resolver.for_body(body)
            if mat is None:
                raise MaterialError(f"body {body.id!r} has no material assigned")
            density = mat.get("physical", {}).get("density")
            if density is None:
                raise MaterialError(
                    f"body {body.id!r} material has no physical.density for mass")
            volume = self._kernel.volume(body.shape)
            cog = self._kernel.signature(body.shape)["cog"]
            bodies_out.append({
                "id": body.id,
                "material": resolver.material_name(body),
                "volume": volume,
                "density": density,
                # density kg/m^3 * volume mm^3 * 1e-9 -> mass kg (see module docstring).
                "mass": density * volume * _MM3_TO_M3,
                "cog": cog,
            })
        return {"bodies": bodies_out, "total": _totals(bodies_out)}


def _totals(bodies: list[dict]) -> dict:
    """Assembly totals: summed mass/volume and the mass-weighted mean COG."""
    total_mass = sum(b["mass"] for b in bodies)
    total_volume = sum(b["volume"] for b in bodies)
    if total_mass > 0:
        cog = tuple(sum(b["mass"] * b["cog"][i] for b in bodies) / total_mass
                    for i in range(3))
    else:
        cog = (0.0, 0.0, 0.0)
    return {"mass": total_mass, "volume": total_volume, "cog": cog}
