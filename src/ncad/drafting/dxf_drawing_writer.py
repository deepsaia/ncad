"""Write a laid-out drawing to a DXF string via ezdxf.

Consumes the same layout dict as the SVG writer and emits a DXF: visible edges on a ``VISIBLE``
layer, hidden edges on a dashed ``HIDDEN`` layer, dimensions as a line + value TEXT on a
``DIMENSIONS`` layer, annotations as TEXT, and a title-block rectangle. DXF is the CAM / laser / CNC
handoff format. Same layout -> identical drawing entities. One class.

DXF uses a y-up coordinate frame, matching the drawing/sheet frame, so points are placed directly
(no flip, unlike SVG).

ezdxf is used for GENERATION only (build a document + write); this writer never reads untrusted DXF.
"""

import io

import ezdxf

_VISIBLE_LAYER = "VISIBLE"
_HIDDEN_LAYER = "HIDDEN"
_DIM_LAYER = "DIMENSIONS"
_TEXT_LAYER = "ANNOTATIONS"
_TEXT_HEIGHT = 3.2


class DxfDrawingWriter:
    """Serializes a laid-out drawing to a DXF string via ezdxf."""

    def to_dxf(self, layout: dict) -> str:
        """Return the DXF text for ``layout`` (views, dimensions, annotations, title block)."""
        doc = ezdxf.new(setup=True)
        doc.layers.add(_VISIBLE_LAYER)
        doc.layers.add(_HIDDEN_LAYER, linetype="DASHED")
        doc.layers.add(_DIM_LAYER)
        doc.layers.add(_TEXT_LAYER)
        msp = doc.modelspace()
        for view in layout.get("views", []):
            self._add_view(msp, view)
        for dimension in layout.get("dimensions", []):
            self._add_dimension(msp, dimension, layout)
        for annotation in layout.get("annotations", []):
            self._add_annotation(msp, annotation, layout)
        self._add_title_block(msp, layout.get("title_block", {}))
        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue()

    def _add_view(self, msp, view: dict) -> None:
        origin = view["origin"]
        for edge in view.get("visible", []):
            self._add_polyline(msp, edge, origin, _VISIBLE_LAYER)
        for edge in view.get("hidden", []):
            self._add_polyline(msp, edge, origin, _HIDDEN_LAYER)

    def _add_polyline(self, msp, edge: list, origin: tuple, layer: str) -> None:
        points = [(origin[0] + p[0], origin[1] + p[1]) for p in edge]
        if len(points) >= 2:
            msp.add_lwpolyline(points, dxfattribs={"layer": layer})

    def _add_dimension(self, msp, dimension: dict, layout: dict) -> None:
        origin = _view_origin(layout, dimension["view"])
        geom = dimension["geometry"]
        a = (origin[0] + geom["from"][0], origin[1] + geom["from"][1])
        b = (origin[0] + geom["to"][0], origin[1] + geom["to"][1])
        msp.add_line(a, b, dxfattribs={"layer": _DIM_LAYER})
        anchor = (origin[0] + geom["text_anchor"][0], origin[1] + geom["text_anchor"][1])
        text = msp.add_text(_fmt_value(dimension["value"]),
                            dxfattribs={"layer": _DIM_LAYER, "height": _TEXT_HEIGHT})
        text.set_placement(anchor)

    def _add_annotation(self, msp, annotation: dict, layout: dict) -> None:
        origin = _view_origin(layout, annotation["view"])
        at = (origin[0] + annotation["at"][0], origin[1] + annotation["at"][1])
        text = msp.add_text(str(annotation["text"]),
                            dxfattribs={"layer": _TEXT_LAYER, "height": _TEXT_HEIGHT})
        text.set_placement(at)

    def _add_title_block(self, msp, title_block: dict) -> None:
        box = title_block.get("box")
        if not box:
            return
        x, y, w, h = box
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        msp.add_lwpolyline(corners, dxfattribs={"layer": _TEXT_LAYER})
        title = title_block.get("title")
        if title:
            text = msp.add_text(str(title), dxfattribs={"layer": _TEXT_LAYER, "height": 4.0})
            text.set_placement((x + 4, y + h / 2.0))


def _view_origin(layout: dict, view_id: str) -> tuple:
    for view in layout.get("views", []):
        if view["id"] == view_id:
            return view["origin"]
    return (0.0, 0.0)


def _fmt_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.2f}"
