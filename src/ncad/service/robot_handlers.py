"""Robot routes: list robots (Physics mode) and serve a robot's tree + joint sweeps.

`RobotsHandler` lists assembly names that carry a `<name>.robot.json`; `RobotHandler` serves that
tree; `RobotSweepsHandler` serves the `<name>.robot_sweeps.json` articulation sweeps. All reuse the
injected ModelCatalog verbatim (mirrors the motion handlers).
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


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
