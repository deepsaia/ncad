from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic
from ncad.diagnostics.validation_report import ValidationReport


def test_empty_report_is_ok():
    r = ValidationReport([])
    assert r.ok is True and r.to_dict() == {"ok": True, "diagnostics": []}


def test_warning_only_is_ok():
    r = ValidationReport([Diagnostic("warning", codes.COUPLING_PRIMARY_MISMATCH, "x", "m")])
    assert r.ok is True


def test_any_error_is_not_ok():
    r = ValidationReport([
        Diagnostic("warning", codes.SKETCH_UNDERCONSTRAINED, "s", "under", stage="build"),
        Diagnostic("error", codes.DUPLICATE_ID, "p.features", "dup 'hole'")])
    assert r.ok is False
    d = r.to_dict()
    assert d["ok"] is False and len(d["diagnostics"]) == 2
