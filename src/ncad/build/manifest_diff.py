"""Compare two geometry-facts manifests into a typed, layered regression delta.

A single geometry byte-hash is brittle (exporter noise) and opaque (cannot say WHAT changed). This
diffs two ``GeometryFacts`` manifests along three independent layers, each with its own stable hash:

- **topology** - solid/face/edge counts + body ids. Changes when the B-rep structure changes
  (a face appears, a body splits) - the signal that selector/connector refs may need re-resolving.
- **geometry** - per-body volume + centroid (rounded). Changes when shape or position moved even if
  the topology is identical.
- **bbox** - the overall bounding box (rounded). Changes when overall size/extent moved.

Hashes are order-stable (sorted-key JSON, values rounded to a fixed tolerance so float noise does
not churn them). ``diff`` returns which layers changed + the per-count delta. Pure data, one class.
"""

import hashlib
import json
from typing import Any

# Round coordinates/volumes to this many decimals before hashing so exporter/float noise below the
# tolerance does not spuriously flip a layer. 6 dp on mm geometry = nanometre stability.
_ROUND = 6


class ManifestDiff:
    """Layered topology/geometry/bbox comparison of two geometry-facts manifests."""

    def diff(self, old: dict, new: dict) -> dict:
        """Return layered delta: topology_changed, geometry_changed, bbox_changed, count_delta."""
        return {
            "topology_changed": self.topology_hash(old) != self.topology_hash(new),
            "geometry_changed": self.geometry_hash(old) != self.geometry_hash(new),
            "bbox_changed": self.bbox_hash(old) != self.bbox_hash(new),
            "count_delta": self._count_delta(old, new),
        }

    def topology_hash(self, manifest: dict) -> str:
        """Hash of the topological structure: counts + the set of body ids (order-independent)."""
        counts = manifest.get("counts", {})
        body_ids = sorted(b.get("id") for b in manifest.get("bodies", []))
        return _hash({"counts": counts, "body_ids": body_ids})

    def geometry_hash(self, manifest: dict) -> str:
        """Hash of per-body volume + centroid (rounded), keyed by body id for stable ordering."""
        bodies = {
            b.get("id"): {
                "volume": _round(b.get("volume")),
                "centroid": _round(b.get("centroid")),
            }
            for b in manifest.get("bodies", [])
        }
        return _hash(bodies)

    def bbox_hash(self, manifest: dict) -> str:
        """Hash of the overall bounding box (min/max/size, rounded)."""
        bbox = manifest.get("bbox", {})
        return _hash({k: _round(bbox.get(k)) for k in ("min", "max", "size")})

    def _count_delta(self, old: dict, new: dict) -> dict:
        """Signed change in each topology count (new - old); only nonzero entries are returned."""
        oc, nc = old.get("counts", {}), new.get("counts", {})
        delta = {k: nc.get(k, 0) - oc.get(k, 0) for k in ("solids", "faces", "edges")}
        return {k: v for k, v in delta.items() if v != 0}


def _round(value: Any) -> Any:
    """Round a number or a list/tuple of numbers to _ROUND decimals; pass other values through."""
    if isinstance(value, (int, float)):
        return round(float(value), _ROUND)
    if isinstance(value, (list, tuple)):
        return [_round(v) for v in value]
    return value


def _hash(payload: Any) -> str:
    """Stable SHA-256 over ``payload`` serialized as sorted-key JSON."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
