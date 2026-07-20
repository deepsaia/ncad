"""A single schema-validation issue, returned as data rather than raised."""

from dataclasses import dataclass

from ncad.diagnostics.diagnostic import Diagnostic


@dataclass(frozen=True)
class SchemaIssue:
    """One schema violation found in a spec.

    :ivar location: Dotted/indexed path to the offending field (e.g.
        ``storeys.0.walls.0.thickness``), or ``"<root>"`` for top-level issues.
    :ivar message: Human-readable description of the violation.
    """

    location: str
    message: str

    def to_diagnostic(self, stage: str, code: str) -> Diagnostic:
        """Map this schema/semantic issue into the unified Diagnostic (error severity)."""
        return Diagnostic(severity="error", code=code, location=self.location,
                          message=self.message, stage=stage)
