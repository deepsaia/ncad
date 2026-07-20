"""POST /api/v1/validate: validate a document spec without building (agent-facing diagnostics).

The static-validation entry for the service: an agent posts a spec and gets the ValidationReport
(``{ok, diagnostics}``) back without paying the geometry cost. A design-invalid document returns
200 with ``ok=false`` (the diagnostics ARE the answer); only a bad request or a disallowed/
unresolvable spec is a 400. Mirrors the build handlers' error contract. One handler class.
"""

import logging

from ncad.service.base_handler import BaseApiHandler
from ncad.viewer.build_service import BuildError

logger = logging.getLogger(__name__)


class ValidateHandler(BaseApiHandler):
    """POST /api/v1/validate -> ValidationReport JSON for the posted spec."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Return the ValidationReport (200, even ok=False); 400 on bad request / bad spec."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            report = self._build_service.validate(spec)
        except BuildError as exc:
            logger.warning("validate rejected for %s: %s", spec, exc)
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected validate failure for %s", spec)
            self.write_error_json(500, "internal validate error")
            return
        self.write_json(200, report)
