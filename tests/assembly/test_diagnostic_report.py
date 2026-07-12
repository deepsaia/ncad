from ncad.assembly.diagnostic_report import DiagnosticReport


def test_report_to_dict_round_trips_fields() -> None:
    r = DiagnosticReport(status="redundant", dof=0, explanation="2 bodies >> 0 free DoF",
                         failing_ids=[], redundant_ids=["m3"], under_constrained_hint=None)
    d = r.to_dict()
    assert d == {"status": "redundant", "dof": 0, "explanation": "2 bodies >> 0 free DoF",
                 "failing_ids": [], "redundant_ids": ["m3"], "under_constrained_hint": None}


def test_report_defaults_are_empty() -> None:
    r = DiagnosticReport(status="well_constrained", dof=0, explanation="x")
    assert r.failing_ids == [] and r.redundant_ids == []
    assert r.under_constrained_hint is None
