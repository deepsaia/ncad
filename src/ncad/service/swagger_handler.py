"""Serve Swagger UI at /docs, pointed at /api/v1/openapi.json.

A tiny self-contained HTML page that loads Swagger UI from a CDN (no build step, like the viewer's
three.js) and renders the interactive docs from our OpenAPI document. Kept a module-level constant
+ one handler class.
"""

from ncad.service.base_handler import BaseApiHandler

_SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ncad API - Swagger UI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css"
        integrity="sha384-wxLW6kwyHktdDGr6Pv1zgm/VGJh99lfUbzSn6HNHBENZlCN7W602k9VkGdxuFvPn"
        crossorigin="anonymous">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"
          integrity="sha384-wmyclcVGX/WhUkdkATwhaK1X1JtiNrr2EoYJ+diV3vj4v6OC5yCeSu+yW13SYJep"
          crossorigin="anonymous"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: "/api/v1/openapi.json",
      dom_id: "#swagger-ui",
    });
  </script>
</body>
</html>
"""


class SwaggerHandler(BaseApiHandler):
    """GET /docs -> Swagger UI (loads /api/v1/openapi.json)."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Serve the Swagger UI HTML page."""
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.safe_finish(_SWAGGER_HTML)
