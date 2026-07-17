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

from ncad.service.spec_handlers import SpecsHandler
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
            URLSpec(r"/api/v1/specs", SpecsHandler, deps),
        ]
        return rules
