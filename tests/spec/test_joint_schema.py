from ncad.spec.assembly_schema_validator import AssemblySchemaValidator


def test_assembly_with_joints_validates() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {
        "instances": [{"id": "base", "file": "p.hocon", "part": "b", "lock": True},
                      {"id": "arm", "file": "p.hocon", "part": "a"}],
        "joints": [
            {"id": "j1", "type": "revolute", "value": 30,
             "between": [{"instance": "base", "connector": "pivot"},
                         {"instance": "arm", "connector": "hub"}]}]}}
    assert AssemblySchemaValidator().validate(doc) == []


def test_duplicate_joint_id_flagged() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "p"}],
        "joints": [
            {"id": "j1", "type": "ball", "between": [{"instance": "a", "connector": "c"},
                                                     {"instance": "a", "connector": "d"}]},
            {"id": "j1", "type": "ball", "between": [{"instance": "a", "connector": "c"},
                                                     {"instance": "a", "connector": "d"}]}]}}
    issues = AssemblySchemaValidator().validate(doc)
    assert any("duplicate joint id" in i.message for i in issues)


def test_joint_id_colliding_with_constraint_id_flagged() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {
        "instances": [{"id": "a", "file": "p.hocon", "part": "p"}],
        "constraints": [{"id": "x1", "type": "lock",
                         "between": [{"instance": "a", "connector": "c"}]}],
        "joints": [{"id": "x1", "type": "ball",
                    "between": [{"instance": "a", "connector": "c"},
                                {"instance": "a", "connector": "d"}]}]}}
    issues = AssemblySchemaValidator().validate(doc)
    assert any("collides" in i.message for i in issues)
