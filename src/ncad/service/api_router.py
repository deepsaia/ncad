"""The single source of truth for the ncad service route table.

``ApiRouter.rules(deps)`` returns the ordered list of Tornado ``URLSpec`` rules, each wired with
the injected collaborators. Ordering matters: Tornado selects a handler by URL pattern alone (in
list order, method-agnostic, patterns auto-anchored with a trailing ``$``, and ``.+`` matches
``/``). The ``POST .../(.+)/delete`` routes MUST therefore be registered before the broad
``GET /api/v1/{models,assembly}/(.+)`` catch-alls, or the delete POSTs would resolve to the
GET-only bytes/detail handler and 405. Live-reload is dev-only, so its ws route is added only when
``deps["dev"]`` is true.
"""

from typing import Any

from tornado.web import URLSpec

from ncad.service.assembly_handlers import (
    AssembliesHandler,
    AssemblyDeleteHandler,
    AssemblyHandler,
)
from ncad.service.build_handlers import (
    AssembleHandler,
    BuildHandler,
    MotionBuildHandler,
    PhysicsBuildHandler,
    RobotCollideHandler,
)
from ncad.service.export_handler import ExportHandler
from ncad.service.livereload_handler import LiveReloadHandler
from ncad.service.model_handlers import ModelBytesHandler, ModelDeleteHandler, ModelsHandler
from ncad.service.motion_handlers import MotionHandler, MotionsHandler
from ncad.service.openapi_handler import OpenApiHandler
from ncad.service.robot_handlers import (
    RobotDeleteHandler,
    RobotHandler,
    RobotKeyframesHandler,
    RobotsHandler,
    RobotSweepsHandler,
)
from ncad.service.sidecar_handlers import (
    BomHandler,
    ElementMapHandler,
    HierarchyHandler,
    PlanHandler,
    StatusHandler,
)
from ncad.service.spec_handlers import SpecsHandler
from ncad.service.static_js_handler import StaticJsHandler
from ncad.service.swagger_handler import SwaggerHandler
from ncad.service.validate_handler import ValidateHandler
from ncad.service.viewer_handler import RootRedirectHandler, ViewerHandler


class ApiRouter:
    """Builds the ordered Tornado route table wired with injected collaborators."""

    def rules(self, deps: dict[str, Any]) -> list[URLSpec]:
        """Return the ordered URLSpec list for the whole service.

        :param deps: The injected collaborators passed to every API handler's ``initialize``
            (catalog, spec_catalog, build_service, page, dev, boot_id).
        """
        rules: list[URLSpec] = [
            URLSpec(r"/", RootRedirectHandler),
            URLSpec(r"/viewer", ViewerHandler, deps),
            URLSpec(r"/viewer/(.+)", ViewerHandler, deps),
            URLSpec(r"/js/(.+)", StaticJsHandler),
            URLSpec(r"/docs", SwaggerHandler, deps),
            URLSpec(r"/api/v1/openapi.json", OpenApiHandler, deps),
            # Static collection routes.
            URLSpec(r"/api/v1/specs", SpecsHandler, deps),
            URLSpec(r"/api/v1/models", ModelsHandler, deps),
            URLSpec(r"/api/v1/assemblies", AssembliesHandler, deps),
            URLSpec(r"/api/v1/motions", MotionsHandler, deps),
            URLSpec(r"/api/v1/robots", RobotsHandler, deps),
            # Detail routes by name.
            URLSpec(r"/api/v1/motion/(.+)", MotionHandler, deps),
            # robot-sweeps before robot: different prefixes, but keep the more specific first.
            URLSpec(r"/api/v1/robot-sweeps/(.+)", RobotSweepsHandler, deps),
            URLSpec(r"/api/v1/robot-keyframes/(.+)", RobotKeyframesHandler, deps),
            # The delete POST must precede the robot GET catch-all (Tornado matches method-agnostic,
            # so POST /robot/foo/delete would otherwise resolve to the GET-only RobotHandler).
            URLSpec(r"/api/v1/robot/(.+)/delete", RobotDeleteHandler, deps),
            URLSpec(r"/api/v1/robot/(.+)", RobotHandler, deps),
            URLSpec(r"/api/v1/bom/(.+)", BomHandler, deps),
            URLSpec(r"/api/v1/plan/(.+)", PlanHandler, deps),
            URLSpec(r"/api/v1/elementmap/(.+)", ElementMapHandler, deps),
            URLSpec(r"/api/v1/hierarchy/(.+)", HierarchyHandler, deps),
            URLSpec(r"/api/v1/status/(.+)", StatusHandler, deps),
            # Build POSTs.
            URLSpec(r"/api/v1/build", BuildHandler, deps),
            URLSpec(r"/api/v1/assemble", AssembleHandler, deps),
            URLSpec(r"/api/v1/motion-build", MotionBuildHandler, deps),
            URLSpec(r"/api/v1/physics-build", PhysicsBuildHandler, deps),
            URLSpec(r"/api/v1/robot-collide", RobotCollideHandler, deps),
            URLSpec(r"/api/v1/export", ExportHandler, deps),
            URLSpec(r"/api/v1/validate", ValidateHandler, deps),
            # CRITICAL ORDER: Tornado matches by URL pattern only (method-agnostic, `$`-anchored,
            # `.+` matches `/`). The delete POSTs MUST precede the GET catch-alls below, or e.g.
            # POST /api/v1/models/foo/delete would match `/api/v1/models/(.+)` and route to the
            # GET-only ModelBytesHandler (405). A GET /api/v1/models/foo does not match `/delete`,
            # so it still falls through to the catch-all correctly.
            URLSpec(r"/api/v1/models/(.+)/delete", ModelDeleteHandler, deps),
            URLSpec(r"/api/v1/assembly/(.+)/delete", AssemblyDeleteHandler, deps),
            URLSpec(r"/api/v1/assembly/(.+)", AssemblyHandler, deps),
            URLSpec(r"/api/v1/models/(.+)", ModelBytesHandler, deps),
        ]
        # Browser live-reload is a dev-only affordance; the ws route is absent in production (so a
        # connect there 404s, and the SPA only opens the socket when window.NCAD_DEV is true).
        if deps.get("dev"):
            ws_args = {"boot_id": deps["boot_id"]}
            rules.append(URLSpec(r"/ws/livereload", LiveReloadHandler, ws_args))
        return rules
