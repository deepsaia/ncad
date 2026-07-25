from ncad.service.build_job import BuildJob


def _job(**over):
    base = dict(id="j1", kind="build", spec="a/b.hocon", status="queued", stage="queued",
                stages_done=0, stages_total=4, message="", result=None, error=None,
                created_at=1000.0, finished_at=None)
    base.update(over)
    return BuildJob(**base)


def test_queued_status_dict_has_no_result_or_error():
    d = _job().to_status_dict()
    assert d["status"] == "queued"
    assert d["kind"] == "build"
    assert d["stage"] == "queued"
    assert d["stages_done"] == 0 and d["stages_total"] == 4
    assert "result" not in d
    assert "error" not in d


def test_done_status_dict_carries_result_only():
    d = _job(status="done", result={"built": ["x"]}, finished_at=1005.0).to_status_dict()
    assert d["status"] == "done"
    assert d["result"] == {"built": ["x"]}
    assert "error" not in d


def test_failed_status_dict_carries_error_only():
    d = _job(status="failed", error="boom", finished_at=1005.0).to_status_dict()
    assert d["error"] == "boom"
    assert "result" not in d


def test_cancelled_status_dict_carries_error():
    d = _job(status="cancelled", error="cancelled by client").to_status_dict()
    assert d["status"] == "cancelled"
    assert d["error"] == "cancelled by client"
