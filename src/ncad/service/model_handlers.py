"""Model routes: list models, serve model bytes, delete a model.

`ModelsHandler` lists models with their recorded source; `ModelBytesHandler` streams a glb/gltf/
bin/png by name (path-traversal-safe via the catalog); `ModelDeleteHandler` deletes a model and
its sidecars. All reuse the injected ModelCatalog verbatim.
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler

_CONTENT_TYPES = {
    ".gltf": "model/gltf+json",
    ".glb": "model/gltf-binary",
    ".bin": "application/octet-stream",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def content_type_for(path: str) -> str:
    """MIME type for a served model file, by extension (defaults to octet-stream)."""
    lowered = path.lower()
    for extension, content_type in _CONTENT_TYPES.items():
        if lowered.endswith(extension):
            return content_type
    return "application/octet-stream"


class ModelsHandler(BaseApiHandler):
    """GET /api/v1/models -> the list of models with recorded sources."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"models": [{"name", "source"}, ...]}``."""
        self.write_json(200, {"models": self._catalog.models_with_sources()})


class ModelBytesHandler(BaseApiHandler):
    """GET /api/v1/models/<name> -> the model (or its buffer/image sidecar) bytes."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved model bytes, or 404 if unknown/unsafe."""
        resolved = self._catalog.resolve(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "unknown model")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", content_type_for(resolved))
            self.safe_finish(handle.read())


class ModelDeleteHandler(BaseApiHandler):
    """POST /api/v1/models/<name>/delete -> delete the model + its sidecars."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Delete the model; return the updated list, or 404 if unknown."""
        removed = self._catalog.delete_model(unquote(args[0]))
        if removed is None:
            self.write_error_json(404, "unknown model")
            return
        self.write_json(200, {"models": self._catalog.models_with_sources()})
