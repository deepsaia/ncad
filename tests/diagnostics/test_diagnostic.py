import pytest

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic, DiagnosticError


def test_to_dict_roundtrips_all_fields():
    d = Diagnostic(severity="error", code=codes.UNRESOLVED_CONNECTOR,
                   location="assembly.joints.0.between.1", message="no connector 'axis' on 'cam'",
                   hint="declare a connector 'axis' on part 'cam'", stage="semantic")
    assert d.to_dict() == {
        "severity": "error", "code": "unresolved_connector",
        "location": "assembly.joints.0.between.1", "message": "no connector 'axis' on 'cam'",
        "hint": "declare a connector 'axis' on part 'cam'", "stage": "semantic"}


def test_hint_defaults_to_none_and_serializes():
    d = Diagnostic(severity="warning", code=codes.COUPLING_PRIMARY_MISMATCH,
                   location="assembly.couplings.0", message="not the driven joint")
    assert d.to_dict()["hint"] is None


def test_rejects_unknown_severity_and_stage():
    with pytest.raises(DiagnosticError):
        Diagnostic(severity="fatal", code=codes.SCHEMA, location="<root>", message="x")
    with pytest.raises(DiagnosticError):
        Diagnostic(severity="error", code=codes.SCHEMA, location="<root>", message="x",
                   stage="nowhere")


def test_codes_are_stable_strings():
    assert codes.GEOMETRY_FAILED == "geometry_failed"
    assert codes.DUPLICATE_ID == "duplicate_id"
    assert codes.SCHEMA == "schema"
