"""POST /api/v1/validate: validate a document spec without building (agent-facing diagnostics).

The static-validation entry for the service: an agent posts a spec and gets the ValidationReport
(``{ok, diagnostics}``) back without paying the geometry cost. Offloaded to the build pool and
awaited directly (validation still imports the kernel-adjacent resolver, so it stays off the loop),
with no job record since the report is a fast, single-shot result. A design-invalid document
returns 200 with ``ok=false`` (the diagnostics ARE the answer); a bad request / disallowed spec is
400. One handler class.
"""

from ncad.service.base_handler import BaseApiHandler


class ValidateHandler(BaseApiHandler):
    """POST /api/v1/validate -> ValidationReport JSON for the posted spec."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Return the ValidationReport (200, even ok=False); 400 on bad request / bad spec."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        out = await self._job_manager.arun_direct("validate", {"spec": spec})
        if not out.get("ok"):
            self.write_error_json(400, out.get("error", "validate failed"))
            return
        self.write_json(200, out["result"])
