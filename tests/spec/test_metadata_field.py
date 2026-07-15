"""Document-level metadata ({description, tags}, extensible) on part + assembly documents."""


def _part(metadata: dict) -> dict:
    return {"schema_version": 2, "units": "mm", "metadata": metadata,
            "parts": {"p": {"profile": "solid", "features": [
                {"id": "sk", "op": "sketch", "plane": "XY",
                 "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
                {"id": "e", "op": "extrude", "profile": "sk", "distance": 5}]}}}


def test_part_document_accepts_metadata() -> None:
    from ncad.spec.schema_validator import SchemaValidator
    doc = _part({"description": "a test plate", "tags": ["fixture", "demo"]})
    assert SchemaValidator().validate(doc) == []


def test_metadata_allows_future_subkeys() -> None:
    from ncad.spec.schema_validator import SchemaValidator
    doc = _part({"description": "d", "tags": ["t"], "author": "future", "revision": 3})
    assert SchemaValidator().validate(doc) == []


def test_assembly_document_accepts_metadata() -> None:
    from ncad.spec.assembly_schema_validator import AssemblySchemaValidator
    doc = {"schema_version": 1, "units": "mm",
           "metadata": {"description": "a test assembly", "tags": ["demo"]},
           "assembly": {"instances": [{"id": "a", "file": "p.hocon", "part": "p"}]}}
    assert AssemblySchemaValidator().validate(doc) == []
