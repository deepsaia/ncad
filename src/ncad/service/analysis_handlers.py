"""Analysis routes: list FEA results (Analysis mode) and serve a result's summary + field mesh.

`AnalysesHandler` lists parts that carry an `<name>.analysis.json`; `AnalysisHandler` serves that
summary; `AnalysisMeshHandler` serves the `<name>.analysis.mesh.json` field mesh the viewer colors.
All reuse the injected ModelCatalog verbatim (mirrors the robot handlers).
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


class AnalysesHandler(BaseApiHandler):
    """GET /api/v1/analyses -> analysis names (parts with a .analysis.json), each with a label."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return ``{"analyses": [{"name", "label", "source"}, ...]}`` (label = peak von Mises)."""
        self.write_json(200, {"analyses": self._catalog.analyses_with_labels()})


class AnalysisHandler(BaseApiHandler):
    """GET /api/v1/analysis/<name> -> the analysis summary JSON (max stress/displacement/SF)."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved .analysis.json, or 404 if the part has no analysis result."""
        resolved = self._catalog.resolve_analysis(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "unknown analysis")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.safe_finish(handle.read())


class AnalysisMeshHandler(BaseApiHandler):
    """GET /api/v1/analysis-mesh/<name> -> the boundary field mesh (points + triangles + fields)."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Stream the resolved .analysis.mesh.json, or 404 if the result has no field mesh."""
        resolved = self._catalog.resolve_analysis_mesh(unquote(args[0]))
        if resolved is None:
            self.write_error_json(404, "unknown analysis mesh")
            return
        with open(resolved, "rb") as handle:
            self.set_header("Content-Type", "application/json")
            self.safe_finish(handle.read())


class AnalysisDeleteHandler(BaseApiHandler):
    """POST /api/v1/analysis/<name>/delete -> delete the analysis result sidecars."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Delete the analysis's summary + mesh sidecars; return the list, or 404 if unknown."""
        removed = self._catalog.delete_analysis(unquote(args[0]))
        if removed is None:
            self.write_error_json(404, "unknown analysis")
            return
        self.write_json(200, {"analyses": self._catalog.analyses_with_labels()})
