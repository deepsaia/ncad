"""Build routes: build a part, compose an assembly, or run a motion study.

Each POST reads a JSON body ``{"spec": ...}``, calls the injected BuildService, and returns the
service result merged with the refreshed catalog listing. Errors follow the shared contract: a
malformed body or missing ``spec`` is 400, a disallowed/failed build (``BuildError``) is 400, and
an unexpected failure is 500 (logged, never leaked). Mirrors the stdlib server's handlers.
"""

import logging

from ncad.service.base_handler import BaseApiHandler
from ncad.viewer.build_service import BuildError

logger = logging.getLogger(__name__)


class BuildHandler(BaseApiHandler):
    """POST /api/v1/build -> build a part spec, return the refreshed model list + build result."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Build the posted spec; 400 on bad request/BuildError, 500 on unexpected failure."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            result = self._build_service.build(spec)
        except BuildError as exc:
            logger.warning("build rejected for %s: %s", spec, exc)
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected build failure for %s", spec)
            self.write_error_json(500, "internal build error")
            return
        self.write_json(200, {"models": self._catalog.models_with_sources(), **result})


class AssembleHandler(BaseApiHandler):
    """POST /api/v1/assemble -> compose an assembly, return the refreshed list + result."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Compose the posted assembly spec; 400 on bad request/BuildError, 500 on failure."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            result = self._build_service.assemble(spec)
        except BuildError as exc:
            logger.warning("assemble rejected for %s: %s", spec, exc)
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected assemble failure for %s", spec)
            self.write_error_json(500, "internal assemble error")
            return
        self.write_json(200, {"assemblies": self._catalog.assembly_names(), **result})


class MotionBuildHandler(BaseApiHandler):
    """POST /api/v1/motion-build -> drive a motion study, return the refreshed list + result."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Run the posted motion spec; 400 on bad request/BuildError, 500 on failure."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            result = self._build_service.build_motion(spec)
        except BuildError as exc:
            logger.warning("motion-build rejected for %s: %s", spec, exc)
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected motion-build failure for %s", spec)
            self.write_error_json(500, "internal motion-build error")
            return
        self.write_json(200, {"motions": self._catalog.motions_with_labels(), **result})
