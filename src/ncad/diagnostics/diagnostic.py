"""The single validation/build issue envelope every ncad layer emits (agent-facing contract).

Replaces the ad-hoc SchemaIssue / BuildIssue / motion-dict shapes: one Diagnostic with a severity,
a machine-readable code (ncad.diagnostics.codes), a location (dotted path OR node id), a message,
an optional fix hint, and the producing stage. to_dict() is the JSON an agent consumes. An invalid
severity/stage raises DiagnosticError (a programmer error, not a document error). One class.
"""

from dataclasses import dataclass

_SEVERITIES = frozenset({"error", "warning", "info"})
_STAGES = frozenset({"schema", "semantic", "build", "motion"})


class DiagnosticError(Exception):
    """A Diagnostic was constructed with an invalid severity or stage (a programmer error)."""


@dataclass(frozen=True)
class Diagnostic:
    """One validation/build issue in the uniform agent-facing envelope."""

    severity: str
    code: str
    location: str
    message: str
    hint: str | None = None
    stage: str = "semantic"

    def __post_init__(self) -> None:
        if self.severity not in _SEVERITIES:
            raise DiagnosticError(
                f"unknown severity {self.severity!r}; expected {sorted(_SEVERITIES)}")
        if self.stage not in _STAGES:
            raise DiagnosticError(f"unknown stage {self.stage!r}; expected {sorted(_STAGES)}")

    def to_dict(self) -> dict:
        """A JSON-serializable record (all fields, hint may be null)."""
        return {"severity": self.severity, "code": self.code, "location": self.location,
                "message": self.message, "hint": self.hint, "stage": self.stage}
