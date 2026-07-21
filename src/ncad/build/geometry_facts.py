"""Collect a part's build-time geometry facts into one serializable manifest.

A GeometryFacts manifest is the cheap, queryable record of what a build produced: overall bounding
box + size, the topological solid/face/edge counts, and per-solid volume / centroid / (optionally)
mass + inertia. It is gathered ONCE from the kernel right after a part builds, then written beside
the part as a ``<part>.facts.json`` sidecar so validation, regression diffs, and the viewer can read
geometry without re-loading the B-rep. Pure collection over the Kernel abstraction; no geometry is
recomputed elsewhere. One class.

Mass/inertia are OPTIONAL: they need per-body material density, so the caller passes an already
computed mass-properties dict (from MassCalculator) when materials resolve, or None to omit them.
"""

from typing import Any


class GeometryFacts:
    """Builds the geometry-facts manifest for one part from kernel queries."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel

    def collect(self, shape: Any, mass_properties: dict | None = None) -> dict:
        """Return the manifest dict for ``shape`` (+ optional mass properties).

        Shape keys: ``bbox`` {min,max,size,center}, ``counts`` {solids,faces,edges}, ``bodies``
        (per-body volume/centroid and, when mass_properties is given, mass/density/inertia), and
        ``totals`` (summed volume + mass, mass-weighted centroid) when mass is present.
        """
        (minx, miny, minz), (maxx, maxy, maxz) = self._kernel.bounding_box(shape)
        size = (maxx - minx, maxy - miny, maxz - minz)
        center = ((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0)
        elements = self._kernel.describe_elements(shape)
        faces = sum(1 for e in elements if e.get("kind") == "face")
        edges = sum(1 for e in elements if e.get("kind") == "edge")
        manifest: dict = {
            "bbox": {
                "min": [minx, miny, minz], "max": [maxx, maxy, maxz],
                "size": list(size), "center": list(center),
            },
            "counts": {
                "solids": self._kernel.solid_count(shape),
                "faces": faces,
                "edges": edges,
            },
            "bodies": self._bodies(shape, mass_properties),
        }
        if mass_properties is not None:
            manifest["totals"] = mass_properties.get("total")
        return manifest

    def _bodies(self, shape: Any, mass_properties: dict | None) -> list[dict]:
        """Per-body volume + centroid, enriched with mass/density/inertia when available."""
        mass_by_id = {}
        if mass_properties is not None:
            mass_by_id = {b["id"]: b for b in mass_properties.get("bodies", [])}
        out: list[dict] = []
        for body in self._kernel.bodies(shape):
            record: dict = {
                "id": body.id,
                "volume": self._kernel.volume(body.shape),
                "centroid": list(self._kernel.signature(body.shape)["cog"]),
            }
            mp = mass_by_id.get(body.id)
            if mp is not None:
                record["material"] = mp.get("material")
                record["density"] = mp.get("density")
                record["mass"] = mp.get("mass")
                record["inertia"] = mp.get("inertia")
            out.append(record)
        return out
