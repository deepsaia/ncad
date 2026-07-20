import textwrap

from ncad.diagnostics import codes
from ncad.diagnostics.document_validator import DocumentValidator


def test_valid_part_is_ok():
    doc = {"units": "mm", "parts": {"p": {"profile": "solid", "features": [
        {"id": "base", "op": "primitive", "kind": "box", "w": 10, "d": 10, "h": 10}]}}}
    assert DocumentValidator().validate(doc).ok is True


def test_part_duplicate_id_reported_not_raised():
    doc = {"units": "mm", "parts": {"p": {"profile": "solid", "features": [
        {"id": "x", "op": "primitive", "kind": "box", "w": 1, "d": 1, "h": 1},
        {"id": "x", "op": "primitive", "kind": "box", "w": 1, "d": 1, "h": 1}]}}}
    report = DocumentValidator().validate(doc)   # must NOT raise
    assert report.ok is False
    assert any(d.code == codes.DUPLICATE_ID for d in report.diagnostics)


def test_part_schema_error_reported():
    doc = {"parts": {}}   # missing required 'units'
    report = DocumentValidator().validate(doc)
    assert report.ok is False
    assert any(d.stage == "schema" for d in report.diagnostics)


def test_motion_missing_assembly_file(tmp_path):
    doc = {"motion": {"assembly": "nope.asm.hocon", "driver": {"joint": "j", "from": 0, "to": 90}}}
    report = DocumentValidator(base_dir=str(tmp_path)).validate(doc)
    assert any(d.code == codes.MOTION_ASSEMBLY_MISSING for d in report.diagnostics)


def test_assembly_bad_connector(tmp_path):
    # write a part file with a known connector, then reference a wrong connector in an assembly.
    (tmp_path / "p.hocon").write_text(textwrap.dedent('''
        units = mm
        parts { arm {
          profile = solid
          connectors = [ { id = tip, at_point = [0,0,0], axis = [0,0,1] } ]
          features = [ { id = b, op = primitive, kind = box, w = 10, d = 10, h = 10 } ]
        } }
    '''))
    doc = {"units": "mm", "assembly": {"instances": [{"id": "a", "file": "p.hocon", "part": "arm"}],
        "joints": [{"id": "j", "type": "revolute", "between": [
            {"instance": "a", "connector": "wrong"}, {"instance": "a", "connector": "tip"}]}]}}
    report = DocumentValidator(base_dir=str(tmp_path)).validate(doc)
    assert any(d.code == codes.UNRESOLVED_CONNECTOR for d in report.diagnostics)
