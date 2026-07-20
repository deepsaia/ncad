"""The result of validating a document: ok + the list of Diagnostics (agent-facing).

ok is True when no diagnostic is error-severity (warnings/info do not block). to_dict() is the JSON
an agent consumes to decide whether to build or to fix and retry. One class.
"""

from dataclasses import dataclass

from ncad.diagnostics.diagnostic import Diagnostic


@dataclass(frozen=True)
class ValidationReport:
    """A document's validation result: ok flag + the diagnostics that produced it."""

    diagnostics: list[Diagnostic]

    @property
    def ok(self) -> bool:
        """True when no diagnostic is error-severity (warnings + info do not block a build)."""
        return not any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict:
        """A JSON-serializable report: ``{"ok": bool, "diagnostics": [...]}``."""
        return {"ok": self.ok, "diagnostics": [d.to_dict() for d in self.diagnostics]}
