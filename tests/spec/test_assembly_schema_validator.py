from ncad.spec.assembly_schema_validator import AssemblySchemaValidator


def _doc(instances):
    return {"units": "mm", "assembly": {"instances": instances}}


def test_valid_assembly_passes() -> None:
    doc = _doc([
        {"id": "a", "file": "parts/p.hocon", "part": "widget"},
        {"id": "b", "file": "parts/p.hocon", "part": "widget",
         "placement": {"position": [10, 0, 0]}},
    ])
    assert AssemblySchemaValidator().validate(doc) == []


def test_missing_required_field_fails() -> None:
    doc = _doc([{"id": "a", "file": "parts/p.hocon"}])  # no `part`
    issues = AssemblySchemaValidator().validate(doc)
    assert issues


def test_duplicate_instance_id_fails() -> None:
    doc = _doc([
        {"id": "a", "file": "parts/p.hocon", "part": "widget"},
        {"id": "a", "file": "parts/p.hocon", "part": "widget"},
    ])
    issues = AssemblySchemaValidator().validate(doc)
    assert any("duplicate" in i.message.lower() for i in issues)
