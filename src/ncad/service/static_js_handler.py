"""Serve the viewer's app JS modules from the package's static/js dir at /js/<name>.

The viewer SPA moved its module out of the HTML into ``src/ncad/viewer/static/js/`` and loads it via
``<script type="module" src="/js/app.js">``. This serves those files (path-traversal safe, .js
only) so ``ncad serve`` mounts them at the same root-absolute ``/js/`` path the stdlib server uses.
"""

from pathlib import Path

from tornado.web import RequestHandler

_STATIC_JS_DIR = (Path(__file__).resolve().parent.parent / "viewer" / "static" / "js")


class StaticJsHandler(RequestHandler):
    """GET /js/<name> -> a viewer JS module from static/js/ (404 outside it or non-.js)."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the requested .js module, or 404 for traversal / unknown / non-.js."""
        candidate = (_STATIC_JS_DIR / args[0]).resolve()
        if (candidate.parent != _STATIC_JS_DIR or candidate.suffix != ".js"
                or not candidate.is_file()):
            self.set_status(404)
            self.finish("unknown script")
            return
        self.set_header("Content-Type", "text/javascript; charset=utf-8")
        self.finish(candidate.read_bytes())
