"""Robot routes: list robots (Physics mode) and serve a robot's tree + joint sweeps.

`RobotsHandler` lists assembly names that carry a `<name>.robot.json`; `RobotHandler` serves that
tree; `RobotSweepsHandler` serves the `<name>.robot_sweeps.json` articulation sweeps. All reuse the
injected ModelCatalog verbatim (mirrors the motion handlers).
"""

import json
from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler
from ncad.viewer.build_service import BuildError


class RobotsHandler(BaseApiHandler):
    """GET /api/v1/robots -> robot names (assemblies with a .robot.json), each with a label."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"robots": [{"name", "label"}, ...]}`` (label = joint count)."""
        self.write_json(200, {"robots": self._catalog.robots_with_labels()})


class RobotHandler(BaseApiHandler):
    """GET /api/v1/robot/<name> -> the robot's tree JSON (links + joints + computed inertia)."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved .robot.json, or 404 if the assembly has no robot export."""
        resolved = self._catalog.resolve_robot(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "unknown robot")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.safe_finish(handle.read())


class RobotSweepsHandler(BaseApiHandler):
    """GET /api/v1/robot-sweeps/<name> -> the per-actuated-joint articulation sweeps JSON."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved .robot_sweeps.json, or 404 if none (sweeps are opt-in at export)."""
        resolved = self._catalog.resolve_robot_sweeps(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "no sweeps for robot")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.safe_finish(handle.read())


class RobotDeleteHandler(BaseApiHandler):
    """POST /api/v1/robot/<name>/delete -> delete the robot sidecars (tree + sweeps)."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Delete the robot's tree + sweeps sidecars; return the list, or 404 if unknown."""
        removed = self._catalog.delete_robot(unquote(args[0]))
        if removed is None:
            self.write_error_json(404, "unknown robot")
            return
        self.write_json(200, {"robots": self._catalog.robots_with_labels()})


class RobotKeyframesHandler(BaseApiHandler):
    """GET/POST /api/v1/robot-keyframes/<name> -> read a robot's saved keyframe sets or save one."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"sets": {name: [{time, pose}], ...}}`` (empty when none saved)."""
        self.write_json(200, self._build_service.read_robot_keyframes(unquote(args[0])))

    def post(self, *args: str, **kwargs: str) -> None:
        """Save (upsert) a named keyframe set; body ``{keyframes: [...], set?: name}``."""
        try:
            body = json.loads(self.request.body or b"{}")
            set_name, keyframes = body.get("set", "default"), body["keyframes"]
        except (ValueError, KeyError, TypeError):
            self.write_error_json(400, "request must be JSON with 'keyframes' (+ optional 'set')")
            return
        try:
            result = self._build_service.save_robot_keyframes(unquote(args[0]), set_name, keyframes)
        except BuildError as exc:
            self.write_error_json(400, str(exc))
            return
        self.write_json(200, result)
