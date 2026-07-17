"""Assembly routes: list assemblies, serve an assembly scene, delete an assembly.

`AssembliesHandler` lists composed scene names; `AssemblyHandler` serves a `<name>.assembly.json`
scene; `AssemblyDeleteHandler` removes a scene (and its motion sidecar). All reuse the injected
ModelCatalog verbatim.
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


class AssembliesHandler(BaseApiHandler):
    """GET /api/v1/assemblies -> the list of composed assembly scene names."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"assemblies": [name, ...]}``."""
        self.write_json(200, {"assemblies": self._catalog.assembly_names()})


class AssemblyHandler(BaseApiHandler):
    """GET /api/v1/assembly/<name> -> the assembly scene JSON."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved scene JSON, or 404 if unknown/unsafe."""
        resolved = self._catalog.resolve_assembly(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "unknown assembly")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.safe_finish(handle.read())


class AssemblyDeleteHandler(BaseApiHandler):
    """POST /api/v1/assembly/<name>/delete -> delete the scene (+ its motion sidecar)."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Delete the assembly scene; return the updated list, or 404 if unknown."""
        removed = self._catalog.delete_assembly(unquote(args[0]))
        if removed is None:
            self.write_error_json(404, "unknown assembly")
            return
        self.write_json(200, {"assemblies": self._catalog.assembly_names()})
