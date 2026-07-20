"""A single build-time issue, returned as data rather than raised (design §10)."""

from dataclasses import dataclass

from ncad.diagnostics.codes import GEOMETRY_FAILED, SKETCH_UNDERCONSTRAINED
from ncad.diagnostics.diagnostic import Diagnostic


@dataclass(frozen=True)
class BuildIssue:
    """One problem encountered while building a feature, tagged by node id.

    :ivar node_id: The ``id`` of the feature/node the issue is attributed to.
    :ivar message: Human-readable description of the problem.
    :ivar level: ``"error"`` (blocks the feature, the default) or ``"warning"`` (the
        feature still builds; used for non-fatal status like an under-constrained sketch).
    """

    node_id: str
    message: str
    level: str = "error"

    def to_diagnostic(self) -> Diagnostic:
        """Map this build issue to a Diagnostic (stage=build; warning -> underconstrained code)."""
        warning = self.level == "warning"
        return Diagnostic(
            severity="warning" if warning else "error",
            code=SKETCH_UNDERCONSTRAINED if warning else GEOMETRY_FAILED,
            location=self.node_id, message=self.message, stage="build")
