"""Assign TopoShape-style persistent names from construction lineage (design section 2).

A name is derived from an element's construction history, not its current position, so it is
stable when geometry changes. The rules, per output element:

- CARRIED (survived the op unchanged): keep the prior name.
- MODIFIED_FROM a single parent: inherit the parent's name (the "same" face, moved or trimmed).
- GENERATED_FROM inputs (fresh topology, e.g. a fillet surface): a fresh content hash that folds
  in the parents' names, so the name changes only if that lineage changes.
- No usable history: a deterministic GEOMETRIC SEED name (used for imported, history-free solids
  and as the fallback when a backend cannot report history).

All hashing is over deterministic strings only (feature id, op, role, sorted parent names,
ordinal) so the same spec produces byte-identical names.
"""

import hashlib
import logging
from typing import Any

from ncad.kernel.element_history import ElementHistory

logger = logging.getLogger(__name__)


def _hash8(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def _round_seq(seq: Any, ndigits: int) -> tuple:
    if seq is None:
        return ()
    return tuple(round(float(v), ndigits) for v in seq)


def geometric_seed_name(kind: str, descriptor: dict, owner: str) -> str:
    """A deterministic name from an element's geometry, for history-free solids."""
    signature = "|".join([
        str(descriptor.get("geom_type")),
        str(_round_seq(descriptor.get("normal"), 3)),
        str(round(float(descriptor.get("area") or descriptor.get("length") or 0.0), 4)),
        str(_round_seq(descriptor.get("center"), 3)),
    ])
    return f"#{kind}/{owner}/{_hash8(signature)}"


class PersistentNamer:
    """Computes persistent names for an op's output elements from its ElementHistory."""

    def name_elements(self, feature_id: str, op_type: str, descriptors: list[dict],
                      tags: dict[int, str], history: ElementHistory | None,
                      prior_by_handle: dict[Any, str]) -> list[str]:
        """Return one persistent name per descriptor, positionally aligned."""
        if history is None:
            # No lineage: seed from geometry (imported solids, un-instrumented ops).
            return [geometric_seed_name(d["kind"], d, feature_id) for d in descriptors]
        names: list[str] = []
        for index, descriptor in enumerate(descriptors):
            handle = descriptor["handle"]
            role = tags.get(index) or descriptor["kind"]
            names.append(self._name_one(feature_id, op_type, descriptor, role, handle,
                                        history, prior_by_handle, index))
        return names

    def _name_one(self, feature_id: str, op_type: str, descriptor: dict, role: str,
                  handle: Any, history: ElementHistory, prior_by_handle: dict[Any, str],
                  ordinal: int) -> str:
        modified_parents = history.modified_from.get(handle)
        generated_parents = history.generated_from.get(handle)
        # MODIFIED from exactly one known parent: inherit its name (same face, changed shape).
        if modified_parents and len(modified_parents) == 1:
            prior = prior_by_handle.get(modified_parents[0])
            if prior is not None:
                return prior
        # CARRIED: not in either map but has a prior name (survived the op unchanged).
        if modified_parents is None and generated_parents is None:
            prior = prior_by_handle.get(handle)
            if prior is not None:
                return prior
        # GENERATED (or modified-from-many/unknown): fresh hash folding the parent names.
        parents = (generated_parents or []) + (modified_parents or [])
        parent_names = sorted(prior_by_handle.get(p, "?") for p in parents)
        payload = "|".join([feature_id, op_type, role, ";".join(parent_names), str(ordinal)])
        return f"#{descriptor['kind']}/{feature_id}/{_hash8(payload)}"
