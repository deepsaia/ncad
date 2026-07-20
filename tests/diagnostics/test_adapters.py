from ncad.diagnostics import codes
from ncad.ops.build_issue import BuildIssue
from ncad.spec.schema_issue import SchemaIssue


def test_schema_issue_to_diagnostic():
    d = SchemaIssue(location="parts.p.features", message="dup 'h'").to_diagnostic(
        stage="semantic", code=codes.DUPLICATE_ID)
    assert d.severity == "error" and d.code == codes.DUPLICATE_ID
    assert d.location == "parts.p.features" and d.stage == "semantic"


def test_build_issue_error_to_diagnostic():
    d = BuildIssue(node_id="fillet_1", message="OCCT failed").to_diagnostic()
    assert d.stage == "build" and d.severity == "error"
    assert d.code == codes.GEOMETRY_FAILED and d.location == "fillet_1"


def test_build_issue_warning_maps_to_underconstrained():
    d = BuildIssue(node_id="sk", message="dof 2", level="warning").to_diagnostic()
    assert d.severity == "warning" and d.code == codes.SKETCH_UNDERCONSTRAINED
