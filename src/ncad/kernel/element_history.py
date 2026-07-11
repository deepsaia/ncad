"""Per-op element lineage: which output sub-shapes came from which inputs.

Populated by a kernel after an op so the naming layer can assign persistent names from
construction history instead of geometry. Keys and values are opaque kernel sub-shape handles
(the same handles ``describe_elements`` returns). An output handle in neither ``generated_from``
nor ``modified_from`` is treated as CARRIED (it survived the op unchanged and keeps its name).
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ElementHistory:
    """Lineage of an op's output relative to its inputs."""

    # output handle -> input handles it was newly generated from (fresh topology, e.g. a
    # fillet's rounded face born from an edge).
    generated_from: dict[Any, list[Any]] = field(default_factory=dict)
    # output handle -> input handles it is a changed continuation of (same face, moved/trimmed).
    modified_from: dict[Any, list[Any]] = field(default_factory=dict)
    # input handles with no survivor in the output.
    deleted: list[Any] = field(default_factory=list)
