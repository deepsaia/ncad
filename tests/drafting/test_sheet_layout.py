"""SheetLayout: ISO sheet sizes, orientation, title-block box, view placement."""

import pytest

from ncad.drafting.sheet_layout import SheetLayout


def test_a3_landscape_dimensions():
    layout = SheetLayout({"size": "A3", "orientation": "landscape"})
    assert (layout.width, layout.height) == (420.0, 297.0)


def test_a4_portrait_dimensions():
    layout = SheetLayout({"size": "A4", "orientation": "portrait"})
    assert (layout.width, layout.height) == (210.0, 297.0)


def test_default_is_a4_landscape():
    layout = SheetLayout({})
    assert (layout.width, layout.height) == (297.0, 210.0)


def test_unknown_size_raises():
    with pytest.raises(ValueError):
        SheetLayout({"size": "A9"})


def test_title_block_box_is_inside_the_sheet():
    layout = SheetLayout({"size": "A3", "orientation": "landscape"})
    x, y, w, h = layout.title_block_box()
    assert x >= 0 and y >= 0
    assert x + w <= layout.width
    assert y + h <= layout.height
