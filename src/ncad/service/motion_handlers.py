"""Motion routes: list assemblies that have a trajectory, and serve one trajectory.

`MotionsHandler` lists assembly names with a `<name>.motion.json`; `MotionHandler` serves that
trajectory JSON. Both reuse the injected ModelCatalog verbatim.
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


class MotionsHandler(BaseApiHandler):
    """GET /api/v1/motions -> the list of assembly names that carry a motion trajectory."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"motions": [name, ...]}``."""
        self.write_json(200, {"motions": self._catalog.motion_names()})


class MotionHandler(BaseApiHandler):
    """GET /api/v1/motion/<name> -> the assembly's motion trajectory JSON."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved trajectory JSON, or 404 if the assembly has no motion."""
        resolved = self._catalog.resolve_motion(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "no motion for assembly")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.finish(handle.read())
