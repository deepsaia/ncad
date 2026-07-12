"""The constraint-status diagnostics of an assembly solve (bucket 5.3).

The 3D analogue of the sketch SketchStatus: a legible interpretation of the numeric solve. Carries
the four-state status (well/under/over/redundant), the free DoF, a plain-language explanation, the
ids of failing and of redundant constraints (attributed by mate id), and an under-constrained hint.
Produced by DofDiagnostics from the solver's raw signals; surfaced in the sidecar, viewer, and CLI.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiagnosticReport:
    """One assembly's constraint-status diagnostics."""

    status: str
    dof: int
    explanation: str
    failing_ids: list[str] = field(default_factory=list)
    redundant_ids: list[str] = field(default_factory=list)
    under_constrained_hint: str | None = None

    def to_dict(self) -> dict:
        """A JSON-serializable record for the assembly scene sidecar."""
        return {
            "status": self.status,
            "dof": self.dof,
            "explanation": self.explanation,
            "failing_ids": list(self.failing_ids),
            "redundant_ids": list(self.redundant_ids),
            "under_constrained_hint": self.under_constrained_hint,
        }
