"""The in-memory record for one submitted build job (data + its status projection). One class."""

from dataclasses import dataclass


@dataclass
class BuildJob:
    """One submitted build: its identity, spec, live status, stage progress, and terminal result.

    ``status`` is one of ``queued``/``running``/``done``/``failed``/``cancelled``. ``result`` is
    set only on ``done`` (the payload the frontend renders); ``error`` on ``failed``/``cancelled``.
    """

    id: str
    kind: str
    spec: str
    status: str
    stage: str
    stages_done: int
    stages_total: int
    message: str
    result: dict | None
    error: str | None
    created_at: float
    finished_at: float | None

    def to_status_dict(self) -> dict:
        """Project to the JSON the status endpoint returns (result/error only when terminal)."""
        out: dict = {
            "status": self.status,
            "kind": self.kind,
            "stage": self.stage,
            "stages_done": self.stages_done,
            "stages_total": self.stages_total,
            "message": self.message,
        }
        if self.status == "done":
            out["result"] = self.result
        if self.status in ("failed", "cancelled"):
            out["error"] = self.error
        return out
