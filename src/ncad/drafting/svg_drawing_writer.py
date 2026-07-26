"""Write a laid-out drawing to an SVG string.

Consumes a plain layout dict (sheet + placed views with visible/hidden 2D polylines + placed
dimensions + annotations + title block) and emits an SVG: visible edges solid, hidden edges dashed,
dimensions as a line + value text, annotations as text, plus the sheet border and title block. Pure:
same layout -> identical SVG. One class.

SVG's y-axis points DOWN, while the drawing/sheet frame is y-up, so every point is flipped against
the sheet height on the way out.
"""

# xml.etree is used for GENERATION only (build elements + tostring); this writer never parses
# untrusted XML, so the stdlib parser's XXE/entity-expansion risks do not apply here.
import xml.etree.ElementTree as ET

_SVG_NS = "http://www.w3.org/2000/svg"
_VISIBLE_STROKE = "#111111"
_HIDDEN_STROKE = "#888888"
_DIM_STROKE = "#0057b7"
_STROKE_WIDTH = "0.35"
_TEXT_SIZE = "3.2"


class SvgDrawingWriter:
    """Serializes a laid-out drawing to an SVG string."""

    def to_svg(self, layout: dict) -> str:
        """Return the SVG for ``layout`` (sheet, views, dimensions, annotations, title block)."""
        width = float(layout["sheet"]["width"])
        height = float(layout["sheet"]["height"])
        svg = ET.Element("svg", {
            "xmlns": _SVG_NS,
            "width": f"{width}mm",
            "height": f"{height}mm",
            "viewBox": f"0 0 {width} {height}",
        })
        self._add_border(svg, width, height)
        for view in layout.get("views", []):
            self._add_view(svg, view, height)
        for dimension in layout.get("dimensions", []):
            self._add_dimension(svg, dimension, layout, height)
        for annotation in layout.get("annotations", []):
            self._add_annotation(svg, annotation, layout, height)
        self._add_title_block(svg, layout.get("title_block", {}), height)
        ET.indent(svg)
        return ET.tostring(svg, encoding="unicode", xml_declaration=True)

    def _add_border(self, svg: ET.Element, width: float, height: float) -> None:
        ET.SubElement(svg, "rect", {
            "x": "0", "y": "0", "width": str(width), "height": str(height),
            "fill": "white", "stroke": _VISIBLE_STROKE, "stroke-width": "0.7"})

    def _add_view(self, svg: ET.Element, view: dict, sheet_h: float) -> None:
        origin = view["origin"]
        for edge in view.get("visible", []):
            self._add_polyline(svg, edge, origin, sheet_h, _VISIBLE_STROKE, dashed=False)
        for edge in view.get("hidden", []):
            self._add_polyline(svg, edge, origin, sheet_h, _HIDDEN_STROKE, dashed=True)

    def _add_polyline(self, svg: ET.Element, edge: list, origin: tuple, sheet_h: float,
                      stroke: str, dashed: bool) -> None:
        points = " ".join(_fmt(_place(p, origin, sheet_h)) for p in edge)
        attrs = {"points": points, "fill": "none", "stroke": stroke,
                 "stroke-width": _STROKE_WIDTH}
        if dashed:
            attrs["stroke-dasharray"] = "2,1.5"
        ET.SubElement(svg, "polyline", attrs)

    def _add_dimension(self, svg: ET.Element, dimension: dict, layout: dict,
                       sheet_h: float) -> None:
        origin = _view_origin(layout, dimension["view"])
        geom = dimension["geometry"]
        a = _place(geom["from"], origin, sheet_h)
        b = _place(geom["to"], origin, sheet_h)
        ET.SubElement(svg, "line", {
            "x1": _n(a[0]), "y1": _n(a[1]), "x2": _n(b[0]), "y2": _n(b[1]),
            "stroke": _DIM_STROKE, "stroke-width": _STROKE_WIDTH})
        anchor = _place(geom["text_anchor"], origin, sheet_h)
        text = ET.SubElement(svg, "text", {
            "x": _n(anchor[0]), "y": _n(anchor[1]),
            "font-size": _TEXT_SIZE, "fill": _DIM_STROKE, "text-anchor": "middle"})
        text.text = _fmt_value(dimension["value"])

    def _add_annotation(self, svg: ET.Element, annotation: dict, layout: dict,
                        sheet_h: float) -> None:
        origin = _view_origin(layout, annotation["view"])
        at = _place(annotation["at"], origin, sheet_h)
        text = ET.SubElement(svg, "text", {
            "x": _n(at[0]), "y": _n(at[1]), "font-size": _TEXT_SIZE, "fill": _VISIBLE_STROKE})
        text.text = str(annotation["text"])

    def _add_title_block(self, svg: ET.Element, title_block: dict, sheet_h: float) -> None:
        box = title_block.get("box")
        if not box:
            return
        x, y, w, h = box
        top = sheet_h - (y + h)  # flip y-up box to SVG top-left
        ET.SubElement(svg, "rect", {
            "x": _n(x), "y": _n(top), "width": _n(w), "height": _n(h),
            "fill": "none", "stroke": _VISIBLE_STROKE, "stroke-width": "0.5"})
        title = title_block.get("title")
        if title:
            label = ET.SubElement(svg, "text", {
                "x": _n(x + 4), "y": _n(top + h / 2.0),
                "font-size": "4", "fill": _VISIBLE_STROKE})
            label.text = str(title)
        scale = title_block.get("scale")
        if scale:
            label = ET.SubElement(svg, "text", {
                "x": _n(x + 4), "y": _n(top + h - 6),
                "font-size": _TEXT_SIZE, "fill": _VISIBLE_STROKE})
            label.text = f"SCALE {scale}"


def _place(point: tuple, origin: tuple, sheet_h: float) -> tuple:
    """View-local (x, y-up) point -> sheet SVG (x, y-down) coordinates."""
    x = origin[0] + point[0]
    y = origin[1] + point[1]
    return (x, sheet_h - y)


def _fmt(point: tuple) -> str:
    return f"{_n(point[0])},{_n(point[1])}"


def _n(value: float) -> str:
    return f"{float(value):.3f}"


def _view_origin(layout: dict, view_id: str) -> tuple:
    for view in layout.get("views", []):
        if view["id"] == view_id:
            return view["origin"]
    return (0.0, 0.0)


def _fmt_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.2f}"
