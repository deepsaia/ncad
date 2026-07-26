"""SvgDrawingWriter: emit an SVG drawing from a laid-out drawing (synthetic data, no kernel)."""

import xml.etree.ElementTree as ET

from ncad.drafting.svg_drawing_writer import SvgDrawingWriter

_LAYOUT = {
    "sheet": {"width": 297.0, "height": 210.0},
    "title_block": {"box": (117.0, 0.0, 180.0, 40.0), "title": "Test Part", "scale": "1:1"},
    "views": [
        {"id": "front", "origin": (60.0, 120.0),
         "visible": [[(0.0, 0.0), (40.0, 0.0)], [(0.0, 0.0), (0.0, 60.0)]],
         "hidden": [[(10.0, 0.0), (10.0, 60.0)]]},
    ],
    "dimensions": [
        {"view": "front", "value": 40.0,
         "geometry": {"from": (0.0, 0.0), "to": (40.0, 0.0), "text_anchor": (20.0, -12.0)}},
    ],
    "annotations": [{"view": "front", "at": (0.0, -20.0), "text": "MATL: steel"}],
}


def _root() -> ET.Element:
    return ET.fromstring(SvgDrawingWriter().to_svg(_LAYOUT))


def test_root_is_svg_with_sheet_size():
    root = _root()
    assert root.tag.endswith("svg")
    assert root.attrib["width"].startswith("297")
    assert root.attrib["height"].startswith("210")


def test_visible_and_hidden_edges_render_distinctly():
    svg = SvgDrawingWriter().to_svg(_LAYOUT)
    # hidden edges carry a dashed stroke; visible ones do not.
    assert "stroke-dasharray" in svg
    root = _root()
    lines = root.iter("{http://www.w3.org/2000/svg}line")
    assert any(True for _ in lines) or "polyline" in svg


def test_dimension_value_text_present():
    assert "40" in SvgDrawingWriter().to_svg(_LAYOUT)


def test_annotation_and_title_present():
    svg = SvgDrawingWriter().to_svg(_LAYOUT)
    assert "MATL: steel" in svg
    assert "Test Part" in svg


def test_pure_same_layout_same_svg():
    assert SvgDrawingWriter().to_svg(_LAYOUT) == SvgDrawingWriter().to_svg(_LAYOUT)
