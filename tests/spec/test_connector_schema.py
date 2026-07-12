from ncad.spec.assembly_schema_validator import AssemblySchemaValidator
from ncad.spec.schema_validator import SchemaValidator


def test_part_with_connectors_validates() -> None:
    doc = {"schema_version": 2, "units": "mm", "parts": {"p": {
        "profile": "solid",
        "connectors": [{"id": "top", "at": "select faces where normal_z > 0.9"}],
        "features": [{"id": "sk", "op": "sketch", "plane": "XY",
                      "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
                     {"id": "ext", "op": "extrude", "profile": "sk", "distance": 5}]}}}
    assert SchemaValidator().validate(doc) == []


def test_instance_with_connect_validates() -> None:
    doc = {"schema_version": 1, "units": "mm", "assembly": {"instances": [
        {"id": "a", "file": "p.hocon", "part": "p"},
        {"id": "b", "file": "p.hocon", "part": "p",
         "connect": {"my": "c1", "to": {"instance": "a", "connector": "c2"}, "flip": True}}]}}
    assert AssemblySchemaValidator().validate(doc) == []
