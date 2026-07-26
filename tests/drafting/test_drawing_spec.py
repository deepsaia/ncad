"""DrawingSpec: parse + validate a .drawing.hocon document."""

import pytest

from ncad.drafting.drawing_spec import DrawingSpec, DrawingSpecError


def _doc() -> dict:
    return {"drawing": {
        "part": "shelf_bracket.hocon",
        "sheet": {"size": "A3", "orientation": "landscape"},
        "views": [
            {"id": "front", "type": "base", "projection": "XY", "at": [60, 180]},
            {"id": "top", "type": "projected", "from": "front", "direction": "up"},
            {"id": "iso", "type": "iso", "at": [320, 60]},
        ],
        "dimensions": [
            {"view": "front", "type": "linear", "between": "select edges where type = 'line'"},
        ],
        "annotations": [{"view": "front", "at": [20, 20], "text": "MATL: steel_1018"}],
        "title_block": {"title": "Shelf Bracket"},
    }}


def test_parses_source_views_and_dims():
    spec = DrawingSpec(_doc())
    assert spec.source == ("part", "shelf_bracket.hocon")
    assert {v["id"] for v in spec.views} == {"front", "top", "iso"}
    assert spec.dimensions[0]["view"] == "front"
    assert spec.annotations[0]["text"] == "MATL: steel_1018"


def test_missing_source_raises():
    with pytest.raises(DrawingSpecError):
        DrawingSpec({"drawing": {"views": [{"id": "front", "type": "base", "projection": "XY"}]}})


def test_projected_view_unknown_parent_raises():
    doc = _doc()
    doc["drawing"]["views"][1]["from"] = "ghost"
    with pytest.raises(DrawingSpecError):
        DrawingSpec(doc)


def test_dimension_unknown_view_raises():
    doc = _doc()
    doc["drawing"]["dimensions"][0]["view"] = "nope"
    with pytest.raises(DrawingSpecError):
        DrawingSpec(doc)


def test_malformed_selector_raises():
    doc = _doc()
    doc["drawing"]["dimensions"][0]["between"] = "not a selector"
    with pytest.raises(DrawingSpecError):
        DrawingSpec(doc)


def test_assembly_source_supported():
    doc = _doc()
    del doc["drawing"]["part"]
    doc["drawing"]["assembly"] = "caster.asm.hocon"
    spec = DrawingSpec(doc)
    assert spec.source == ("assembly", "caster.asm.hocon")
