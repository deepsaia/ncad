from ncad.spec.assembly_schema_validator import AssemblySchemaValidator


def test_assembly_with_constraints_validates() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {
        "instances": [
            {"id": "base", "file": "p.hocon", "part": "plate", "lock": True},
            {"id": "arm", "file": "p.hocon", "part": "lever"}],
        "constraints": [
            {"id": "m1", "type": "concentric",
             "between": [{"instance": "base", "connector": "pivot"},
                         {"instance": "arm", "connector": "hub"}]},
            {"id": "m2", "type": "angle", "value": 30,
             "between": [{"instance": "base", "connector": "face"},
                         {"instance": "arm", "connector": "face"}]}]}}
    assert AssemblySchemaValidator().validate(doc) == []


def test_duplicate_constraint_id_is_flagged() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "p"}],
        "constraints": [
            {"id": "m1", "type": "lock", "between": [{"instance": "a", "connector": "c"}]},
            {"id": "m1", "type": "lock", "between": [{"instance": "a", "connector": "c"}]}]}}
    issues = AssemblySchemaValidator().validate(doc)
    assert any("duplicate constraint id" in i.message for i in issues)
