"""DrawingDocument: end-to-end ncad draw on a real part (kernel-bound, slow)."""

import io
from pathlib import Path

import ezdxf
import pytest

from ncad.cli.viewer_cli import ViewerCli


@pytest.mark.slow
def test_draw_shelf_bracket_writes_svg_and_dxf(tmp_path):
    result = ViewerCli().draw_document(
        "examples/11-drafting/shelf_bracket.drawing.hocon", str(tmp_path))
    svg = result.get("svg")
    dxf = result.get("dxf")
    assert svg and Path(svg).is_file()
    assert dxf and Path(dxf).is_file()
    # Artifacts land under out/drawings/<name>/
    assert "/drawings/" in svg.replace("\\", "/")


@pytest.mark.slow
def test_drawn_svg_is_wellformed_and_has_edges(tmp_path):
    result = ViewerCli().draw_document(
        "examples/11-drafting/shelf_bracket.drawing.hocon", str(tmp_path))
    svg = Path(result["svg"]).read_text()
    assert svg.lstrip().startswith("<?xml") or svg.lstrip().startswith("<svg")
    assert "polyline" in svg  # projected view edges


@pytest.mark.slow
def test_drawn_dxf_reads_back_with_layers(tmp_path):
    result = ViewerCli().draw_document(
        "examples/11-drafting/shelf_bracket.drawing.hocon", str(tmp_path))
    doc = ezdxf.read(io.StringIO(Path(result["dxf"]).read_text()))
    layers = {layer.dxf.name for layer in doc.layers}
    assert "VISIBLE" in layers


@pytest.mark.slow
def test_svg_only_format(tmp_path):
    result = ViewerCli().draw_document(
        "examples/11-drafting/shelf_bracket.drawing.hocon", str(tmp_path), formats=("svg",))
    assert result.get("svg") is not None
    assert result.get("dxf") is None
