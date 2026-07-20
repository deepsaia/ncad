from ncad.diagnostics import codes
from ncad.diagnostics.checks.assembly_reference_check import AssemblyReferenceCheck


def _doc(joints):
    return {"assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "arm"},
                      {"id": "b", "file": "p.hocon", "part": "base"}],
        "joints": joints}}


_CONN = {"arm": {"tip"}, "base": {"pivot"}}


def test_valid_reference_yields_nothing():
    doc = _doc([{"id": "j", "type": "revolute", "between": [
        {"instance": "a", "connector": "tip"}, {"instance": "b", "connector": "pivot"}]}])
    assert AssemblyReferenceCheck().check(doc, _CONN) == []


def test_unresolved_connector_flagged():
    doc = _doc([{"id": "j", "type": "revolute", "between": [
        {"instance": "a", "connector": "nope"}, {"instance": "b", "connector": "pivot"}]}])
    diags = AssemblyReferenceCheck().check(doc, _CONN)
    assert [d.code for d in diags] == [codes.UNRESOLVED_CONNECTOR]
    assert "nope" in diags[0].message and diags[0].severity == "error"


def test_unknown_instance_in_between_flagged():
    doc = _doc([{"id": "j", "type": "revolute", "between": [
        {"instance": "ghost", "connector": "tip"}, {"instance": "b", "connector": "pivot"}]}])
    assert AssemblyReferenceCheck().check(doc, _CONN)[0].code == codes.UNRESOLVED_CONNECTOR


def test_missing_instance_part_flagged():
    doc = {"assembly": {"instances": [{"id": "a", "file": "p.hocon", "part": "ghostpart"}],
                        "joints": []}}
    diags = AssemblyReferenceCheck().check(doc, _CONN)
    assert [d.code for d in diags] == [codes.MISSING_INSTANCE_PART]


def test_unknown_joint_type_flagged():
    doc = _doc([{"id": "j", "type": "wobble", "between": [
        {"instance": "a", "connector": "tip"}, {"instance": "b", "connector": "pivot"}]}])
    diags = AssemblyReferenceCheck().check(doc, _CONN)
    assert any(d.code == codes.UNKNOWN_JOINT_TYPE for d in diags)
