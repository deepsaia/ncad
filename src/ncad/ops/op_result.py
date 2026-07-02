"""The uniform result of a feature op: shape, provenance, and issues."""

from dataclasses import dataclass, field
from typing import Any

from ncad.ops.build_issue import BuildIssue


@dataclass(frozen=True)
class OpResult:
    """What every feature op returns.

    :ivar shape: The output geometry handle (kernel-opaque), or ``None`` on failure.
    :ivar provenance: Map from output-element tag to the feature ``id`` that produced
        it. Bucket 0.1 records the producing feature per shape; it grows into the full
        element map in later buckets (design §2).
    :ivar issues: Build issues attributed to node ids; empty means clean.
    """

    shape: Any
    provenance: dict[str, str] = field(default_factory=dict)
    issues: list[BuildIssue] = field(default_factory=list)
