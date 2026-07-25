"""Build routes: submit a part/assembly/motion/physics/analysis build as an async job.

Each POST reads a JSON body ``{"spec": ...}``, submits a job to the injected JobManager, and
returns ``202 {job_id}`` immediately so the Tornado loop is never blocked by the build; the client
polls ``GET /api/v1/jobs/<id>`` for stage progress + the result. A malformed body is 400; a
saturated pool + queue is 503 (SaturatedError). RobotCollideHandler is the live posing-panel check;
it is offloaded but awaited directly (no job record) so a drag stays responsive.
"""

import json
import logging

from ncad.service.base_handler import BaseApiHandler
from ncad.service.job_manager import SaturatedError

logger = logging.getLogger(__name__)


class BuildHandler(BaseApiHandler):
    """POST /api/v1/build -> submit a part-build job; 202 {job_id}."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Submit the posted spec as a build job; 400 bad body, 503 when saturated."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            job = self._job_manager.submit("build", {"spec": spec}, coalesce_key=spec)
        except SaturatedError as exc:
            self.write_error_json(503, str(exc))
            return
        self.write_json(202, {"job_id": job.id})


class AssembleHandler(BaseApiHandler):
    """POST /api/v1/assemble -> submit an assembly-compose job; 202 {job_id}."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Submit the posted assembly spec as a job; 400 bad body, 503 when saturated."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            job = self._job_manager.submit("assemble", {"spec": spec}, coalesce_key=spec)
        except SaturatedError as exc:
            self.write_error_json(503, str(exc))
            return
        self.write_json(202, {"job_id": job.id})


class MotionBuildHandler(BaseApiHandler):
    """POST /api/v1/motion-build -> submit a motion-study job; 202 {job_id}."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Submit the posted motion spec as a job; 400 bad body, 503 when saturated."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            job = self._job_manager.submit("motion", {"spec": spec}, coalesce_key=spec)
        except SaturatedError as exc:
            self.write_error_json(503, str(exc))
            return
        self.write_json(202, {"job_id": job.id})


class PhysicsBuildHandler(BaseApiHandler):
    """POST /api/v1/physics-build -> submit a robot-export job; 202 {job_id}."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Submit the posted physics spec as a job; 400 bad body, 503 when saturated."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            job = self._job_manager.submit("physics", {"spec": spec}, coalesce_key=spec)
        except SaturatedError as exc:
            self.write_error_json(503, str(exc))
            return
        self.write_json(202, {"job_id": job.id})


class AnalyzeHandler(BaseApiHandler):
    """POST /api/v1/analyze -> submit an FEA load-case job; 202 {job_id}."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Submit the posted analysis spec as a job; 400 bad body, 503 when saturated."""
        spec = self.load_spec_body()
        if spec is None:
            self.write_error_json(400, "request must be JSON with a 'spec' field")
            return
        try:
            job = self._job_manager.submit("analyze", {"spec": spec}, coalesce_key=spec)
        except SaturatedError as exc:
            self.write_error_json(503, str(exc))
            return
        self.write_json(202, {"job_id": job.id})


class RobotCollideHandler(BaseApiHandler):
    """POST /api/v1/robot-collide -> non-adjacent self-collisions of a robot at a posed config."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Check the posted robot ``name`` at ``pose``; 400 on bad request/BuildError, 500 else."""
        from ncad.viewer.build_service import BuildError

        try:
            body = json.loads(self.request.body or b"{}")
            name, pose = body["name"], body.get("pose", {})
        except (ValueError, KeyError, TypeError):
            self.write_error_json(400, "request must be JSON with 'name' + 'pose'")
            return
        try:
            result = self._build_service.check_robot_collision(name, pose)
        except BuildError as exc:
            logger.warning("robot-collide rejected for %s: %s", name, exc)
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected robot-collide failure for %s", name)
            self.write_error_json(500, "internal robot-collide error")
            return
        self.write_json(200, result)
