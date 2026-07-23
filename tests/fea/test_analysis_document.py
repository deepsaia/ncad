import os

import pytest

from ncad.fea.analysis_document import AnalysisDocument

_BRACKET = os.path.join(os.path.dirname(__file__), "..", "..",
                        "examples", "10-fea", "bracket.analysis.hocon")


def test_run_reports_skipped_without_ccx(tmp_path):
    # gmsh is present in dev; ccx is not -> the run meshes + decks, then reports skipped at solve.
    pytest.importorskip("gmsh")
    result = AnalysisDocument().run(_BRACKET, str(tmp_path))
    assert result["status"] in ("skipped", "generated")
    # The deck must have been written regardless of ccx availability.
    assert os.path.isfile(result["artifact"])


def test_run_without_gmsh_is_skipped(monkeypatch, tmp_path):
    # Simulate the extra being absent: the mesh stage must degrade to skipped, not raise.
    import ncad.fea.gmsh_mesher as gm

    def _no_gmsh(*args, **kwargs):
        raise ImportError("No module named 'gmsh'")

    monkeypatch.setattr(gm.GmshMesher, "mesh", _no_gmsh)
    result = AnalysisDocument().run(_BRACKET, str(tmp_path))
    assert result["status"] == "skipped"


def test_end_to_end_solve_matches_expectation(tmp_path):
    pytest.importorskip("gmsh")
    from ncad.fea.ccx_locator import CcxLocator
    if CcxLocator().locate() is None:
        pytest.skip("CalculiX (ccx) not installed; end-to-end solve skipped")
    result = AnalysisDocument().run(_BRACKET, str(tmp_path))
    assert result["status"] == "generated"
    assert result["summary"]["max_von_mises"] > 0
    assert os.path.isfile(result["sidecars"]["json"])
    assert os.path.isfile(result["sidecars"]["vtk"])
