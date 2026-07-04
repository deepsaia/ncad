"""The uniform result of a feature op: shape, provenance, and issues."""

from dataclasses import dataclass, field
from typing import Any

from ncad.ops.build_issue import BuildIssue


@dataclass(frozen=True)
class OpResult:
    """What every feature op returns.

    :ivar shape: The output geometry handle (kernel-opaque), or ``None`` on failure.
    :ivar provenance: Legacy per-op map, retained for signature compatibility and now
        left empty by ops. Element provenance lives in the Builder's ElementMap as of
        bucket 0.3 (design §2); the Builder does not read this field.
    :ivar issues: Build issues attributed to node ids; empty means clean.
    """

    shape: Any
    provenance: dict[str, str] = field(default_factory=dict)
    issues: list[BuildIssue] = field(default_factory=list)
