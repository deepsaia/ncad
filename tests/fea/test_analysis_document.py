import os

import pytest

from ncad.fea.analysis_document import AnalysisDocument, _step_families


def test_step_families_separate_thermal_from_structural():
    steps = [{"name": "s", "procedure": "static"},
             {"name": "m", "procedure": "frequency"},
             {"name": "h", "procedure": "heat_transfer"}]
    families = _step_families(steps)
    assert [s["name"] for s in families["structural"]] == ["s", "m"]
    assert [s["name"] for s in families["thermal"]] == ["h"]


def test_step_families_omits_absent_family():
    families = _step_families([{"name": "s", "procedure": "static"}])
    assert set(families) == {"structural"}

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


def test_writes_mesh_sidecar_with_fields(tmp_path):
    pytest.importorskip("gmsh")
    from ncad.fea.ccx_locator import CcxLocator
    if CcxLocator().locate() is None:
        pytest.skip("CalculiX (ccx) not installed")
    import json
    result = AnalysisDocument().run(_BRACKET, str(tmp_path))
    mesh_path = result["sidecars"]["mesh"]
    data = json.loads(open(mesh_path).read())
    assert data["points"] and data["triangles"]
    assert "von_mises" in data["fields"]
    assert "von_mises" in data["ranges"]


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


def test_step_families_excludes_fatigue():
    steps = [{"name": "s", "procedure": "static"},
             {"name": "life", "procedure": "fatigue", "of": "s", "ratio": -1.0}]
    families = _step_families(steps)
    assert "life" not in [st["name"] for fam in families.values() for st in fam]
    assert [st["name"] for st in families["structural"]] == ["s"]


def test_fatigue_post_process_merges_into_summary():
    # Unit-level: the fatigue helper adds cycles + safety to a summary from a peak + material.
    from ncad.fea.analysis_document import _run_fatigue
    merged = {"max_von_mises": 600e6}
    steps = [{"name": "s", "procedure": "static"},
             {"name": "life", "procedure": "fatigue", "of": "s", "ratio": -1.0}]
    material = {"structural": {"ultimate": 440e6, "endurance_limit": 220e6,
                               "fatigue_strength_coeff": 1200e6, "fatigue_exponent": -0.085}}
    _run_fatigue(steps, merged, material)
    assert merged["cycles_to_failure"] is not None
    assert merged["fatigue_safety_factor"] is not None
    assert merged["infinite_life"] is False


def test_fatigue_of_unknown_static_step_raises():
    from ncad.fea.analysis_document import _run_fatigue
    from ncad.fea.analysis_error import AnalysisError
    merged = {"max_von_mises": 100e6}
    steps = [{"name": "life", "procedure": "fatigue", "of": "nope", "ratio": -1.0}]
    material = {"structural": {"ultimate": 440e6, "endurance_limit": 220e6,
                               "fatigue_strength_coeff": 1200e6, "fatigue_exponent": -0.085}}
    with pytest.raises(AnalysisError):
        _run_fatigue(steps, merged, material)
