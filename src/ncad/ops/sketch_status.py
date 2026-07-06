"""The constraint status of one sketch feature (design section 5, bucket 1.5).

Carries a sketch's solve outcome as first-class data (distinct from the problem-oriented
BuildIssue channel): the feature id, the status (well/under/over/inconsistent), the
remaining degrees of freedom, and the ids of any failing constraints. Produced by SketchOp
from the SolveResult and surfaced in the viewer and CLI.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SketchStatus:
    """One sketch feature's constraint status."""

    feature_id: str
    status: str
    dof: int
    failing_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """A JSON-serializable record for the status sidecar."""
        return {
            "feature_id": self.feature_id,
            "status": self.status,
            "dof": self.dof,
            "failing_ids": list(self.failing_ids),
        }
