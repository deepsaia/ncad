import json

from ncad.service.build_worker import STAGES, ProgressWriter, run_build


def test_stages_cover_all_kinds():
    assert set(STAGES) == {"build", "assemble", "motion", "physics", "analyze"}
    assert STAGES["analyze"] == ["meshing", "writing deck", "solving (CalculiX)", "reading results"]


def test_progress_writer_writes_atomic_json(tmp_path):
    path = str(tmp_path / "j1.progress.json")
    writer = ProgressWriter(path, "analyze")
    writer.stage("meshing", "con_rod - meshing")
    data = json.loads(open(path).read())
    assert data["stage"] == "meshing"
    assert data["stages_done"] == 1
    assert data["stages_total"] == 4
    assert data["message"] == "con_rod - meshing"
    writer.stage("solving (CalculiX)", "con_rod - solving")
    data = json.loads(open(path).read())
    assert data["stage"] == "solving (CalculiX)"
    assert data["stages_done"] == 3   # index 2 (0-based) + 1


def test_run_build_reports_failure_as_data(tmp_path):
    # A disallowed spec raises BuildError inside the service; run_build must catch and
    # return {"ok": False, "error": ...}, never raise (the pool Future would else carry it).
    progress = str(tmp_path / "j.progress.json")
    out = run_build("build", {"spec": "/nonexistent/not-allowed.hocon"},
                    str(tmp_path), "", progress)
    assert out["ok"] is False
    assert isinstance(out["error"], str) and out["error"]


def test_run_build_unknown_kind_is_failure(tmp_path):
    out = run_build("bogus", {"spec": "x"}, str(tmp_path), "", str(tmp_path / "p.json"))
    assert out["ok"] is False
    assert "unknown build kind" in out["error"]
