"""DxfDrawingWriter: emit a DXF drawing from a laid-out drawing (synthetic data, no kernel)."""

import io

import ezdxf

from ncad.drafting.dxf_drawing_writer import DxfDrawingWriter

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


def _doc():
    text = DxfDrawingWriter().to_dxf(_LAYOUT)
    return ezdxf.read(io.StringIO(text))


def test_dxf_reads_back_with_visible_and_hidden_layers():
    doc = _doc()
    layers = {layer.dxf.name for layer in doc.layers}
    assert "VISIBLE" in layers
    assert "HIDDEN" in layers


def test_visible_lines_on_visible_layer():
    doc = _doc()
    msp = doc.modelspace()
    visible = [e for e in msp if e.dxf.layer == "VISIBLE"]
    assert visible, "the drawing has visible edges on the VISIBLE layer"


def test_dimension_text_present():
    doc = _doc()
    msp = doc.modelspace()
    texts = [e.dxf.text for e in msp.query("TEXT")]
    assert any("40" in t for t in texts)


def _entities(text):
    """The drawing entities as comparable tuples (layer, type, geometry) from a DXF string.

    ezdxf stamps a fresh fingerprint GUID + a version-and-timestamp string into every write, so the
    raw DXF text is never byte-identical between runs. The GEOMETRY the writer produces is
    deterministic, though; compare the modelspace entities, not the container bytes.
    """
    doc = ezdxf.read(io.StringIO(text))
    out = []
    for e in doc.modelspace():
        kind = e.dxftype()
        if kind == "LWPOLYLINE":
            geom = tuple((round(p[0], 6), round(p[1], 6)) for p in e.get_points("xy"))
        elif kind == "LINE":
            geom = ((round(e.dxf.start.x, 6), round(e.dxf.start.y, 6)),
                    (round(e.dxf.end.x, 6), round(e.dxf.end.y, 6)))
        elif kind == "TEXT":
            geom = (e.dxf.text, (round(e.dxf.insert.x, 6), round(e.dxf.insert.y, 6)))
        else:
            geom = None
        out.append((e.dxf.layer, kind, geom))
    return out


def test_pure_same_layout_same_entities():
    # Same layout -> identical drawing entities (the container's GUID/timestamp differ by design).
    first = _entities(DxfDrawingWriter().to_dxf(_LAYOUT))
    second = _entities(DxfDrawingWriter().to_dxf(_LAYOUT))
    assert first == second
