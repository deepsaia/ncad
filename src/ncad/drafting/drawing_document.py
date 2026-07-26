"""Orchestrate a .drawing.hocon into SVG + DXF drawing artifacts.

The drafting counterpart of AnalysisDocument: load the drawing overlay, build its referenced part,
project each view via HLR, resolve each selector-anchored dimension against the built element map,
lay the views + dimensions + title block onto the sheet, and write the requested formats into
out/drawings/<name>/. One class.
"""

import logging
from pathlib import Path
from typing import Any

from ncad.build.builder import Builder
from ncad.build.output_layout import OutputLayout
from ncad.drafting.dimension_resolver import DimensionResolver
from ncad.drafting.drawing_spec import DrawingSpec, DrawingSpecError
from ncad.drafting.dxf_drawing_writer import DxfDrawingWriter
from ncad.drafting.sheet_layout import SheetLayout
from ncad.drafting.svg_drawing_writer import SvgDrawingWriter
from ncad.drafting.view_projector import ViewProjector
from ncad.ops.op_registry import OpRegistry
from ncad.refs.selector import Selector
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class DrawingDocument:
    """Builds SVG + DXF drawings from a .drawing.hocon overlay on a built part."""

    def __init__(self, kernel: Any) -> None:
        """:param kernel: the geometry kernel (provides hlr_view + the build ops)."""
        self._kernel = kernel
        self._projector = ViewProjector(kernel)
        self._resolver = DimensionResolver()
        self._selector = Selector()

    def run(self, drawing_path: str, out_dir: str,
            formats: tuple[str, ...] = ("svg", "dxf")) -> dict:
        """Build the drawing and write the requested formats.

        :param drawing_path: path to the .drawing.hocon document.
        :param out_dir: the models root; artifacts go to ``<out_dir>/drawings/<name>/``.
        :param formats: which outputs to write (subset of ``svg``, ``dxf``).
        :return: ``{"svg": path|None, "dxf": path|None, "warnings": [...]}``.
        """
        document = SpecLoader().load(drawing_path)
        spec = DrawingSpec(document)
        kind, source_path = spec.source
        if kind != "part":
            raise DrawingSpecError(f"drawing source kind {kind!r} is not supported yet (part only)")

        shape, element_map = self._build_part(drawing_path, source_path)
        layout, warnings = self._compose(spec, shape, element_map)

        name = Path(drawing_path).name.split(".")[0]
        target_dir = OutputLayout(out_dir).dir_for("drawings", name)
        target_dir.mkdir(parents=True, exist_ok=True)
        written: dict = {"svg": None, "dxf": None, "warnings": warnings}
        if "svg" in formats:
            svg_path = target_dir / f"{name}.drawing.svg"
            svg_path.write_text(SvgDrawingWriter().to_svg(layout), encoding="utf-8")
            written["svg"] = str(svg_path)
        if "dxf" in formats:
            dxf_path = target_dir / f"{name}.drawing.dxf"
            dxf_path.write_text(DxfDrawingWriter().to_dxf(layout), encoding="utf-8")
            written["dxf"] = str(dxf_path)
        return written

    def _build_part(self, drawing_path: str, source_path: str) -> tuple[Any, Any]:
        """Build the referenced part document; return its solid + final element map."""
        part_file = str(Path(drawing_path).parent / source_path)
        document = SpecLoader().load(part_file)
        parts = document.get("parts") or {}
        if not parts:
            raise DrawingSpecError(f"drawing source {source_path!r} has no parts")
        part = next(iter(parts.values()))
        builder = Builder(self._kernel, OpRegistry.with_defaults())
        result, element_map, _ = builder.build_part_mapped(
            part, base_dir=str(Path(part_file).parent))
        if result.shape is None:
            raise DrawingSpecError(f"drawing source {source_path!r} did not build")
        return result.shape, element_map

    def _compose(self, spec: DrawingSpec, shape: Any, element_map: Any) -> tuple[dict, list]:
        """Project every view + resolve every dimension into a sheet layout dict."""
        sheet = SheetLayout(spec.sheet)
        warnings: list = []
        views_by_id = {view["id"]: view for view in spec.views}

        laid_views: list = []
        for view in spec.views:
            parent = views_by_id.get(view.get("from")) if view["type"] == "projected" else None
            projected = self._projector.project(shape, view, parent=parent)
            laid_views.append({
                "id": view["id"],
                "origin": tuple(view.get("at", (20.0, 20.0))),
                "visible": projected["visible"],
                "hidden": projected["hidden"],
            })

        dimensions = self._resolve_dimensions(spec, shape, element_map, views_by_id, warnings)
        layout = {
            "sheet": {"width": sheet.width, "height": sheet.height},
            "title_block": {"box": sheet.title_block_box(), **spec.title_block},
            "views": laid_views,
            "dimensions": dimensions,
            "annotations": [dict(a) for a in spec.annotations],
        }
        return layout, warnings

    def _resolve_dimensions(self, spec: DrawingSpec, shape: Any, element_map: Any,
                            views_by_id: dict, warnings: list) -> list:
        """Resolve each dimension's selector, project its edges into the view, and measure."""
        resolved: list = []
        for dimension in spec.dimensions:
            view = views_by_id[dimension["view"]]
            parent = views_by_id.get(view.get("from")) if view["type"] == "projected" else None
            edges = self._projected_selection(dimension, shape, element_map, view, parent)
            if not edges:
                warnings.append(f"dimension in view '{dimension['view']}' matched no geometry")
                continue
            measured = self._measure(dimension, edges)
            if measured is None:
                continue
            resolved.append({"view": dimension["view"], "type": dimension["type"], **measured})
        return resolved

    def _projected_selection(self, dimension: dict, shape: Any, element_map: Any,
                             view: dict, parent: dict | None) -> list:
        """The 2D polylines of the edges a dimension's selector matches, projected into its view."""
        query = dimension.get("between") or dimension.get("of")
        if not query:
            return []
        elements = self._selector.select(query, element_map.elements())
        selected_edges = [element.handle for element in elements]
        if not selected_edges:
            return []
        # Project just the selected edges through the SAME view direction as the view's HLR.
        return self._projector.project_edges(selected_edges, view, parent=parent)

    def _measure(self, dimension: dict, edges: list) -> dict | None:
        kind = dimension["type"]
        if kind == "linear" and len(edges) >= 2:
            return self._resolver.measure_linear(edges)
        if kind == "diameter" and edges:
            return self._resolver.measure_diameter(edges[0])
        if kind == "radius" and edges:
            return self._resolver.measure_radius(edges[0])
        return None
