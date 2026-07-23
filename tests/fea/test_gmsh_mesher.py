import os

import pytest

pytest.importorskip("gmsh")

from ncad.build.document_builder import DocumentBuilder  # noqa: E402
from ncad.fea.gmsh_mesher import GmshMesher  # noqa: E402
from ncad.kernel.build123d_kernel import Build123dKernel  # noqa: E402

_BRACKET = os.path.join(os.path.dirname(__file__), "..", "..",
                        "examples", "10-fea", "bracket.hocon")


def _bracket_step(tmp_path):
    kernel = Build123dKernel()
    shape, _ = DocumentBuilder(kernel).resolve_part_builds(_BRACKET)["bracket"]
    step = str(tmp_path / "bracket.step")
    kernel.export(shape, step)
    return step


def test_meshes_bracket_with_named_groups(tmp_path):
    step = _bracket_step(tmp_path)
    out = str(tmp_path / "bracket.inp")
    report = GmshMesher().mesh(
        step, {"element_size": 5.0, "order": 2, "min_quality": 0.0},
        {"root": {"face": "bottom"}, "tip": {"face": "top"}}, out)

    assert report["nodes"] > 0 and report["elements"] > 0
    assert report["element_type"] == "C3D10"
    assert report["groups"]["root"] and report["groups"]["tip"]
    text = open(out).read()
    assert "*NODE" in text and "C3D10" in text
    assert "ELSET=root" in text.replace(" ", "") or "ELSET=ROOT" in text.upper().replace(" ", "")


def test_linear_order_writes_c3d4(tmp_path):
    step = _bracket_step(tmp_path)
    out = str(tmp_path / "bracket.inp")
    report = GmshMesher().mesh(
        step, {"element_size": 8.0, "order": 1, "min_quality": 0.0},
        {"root": {"face": "bottom"}}, out)
    assert report["element_type"] == "C3D4"
