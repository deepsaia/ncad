"""Tests for the schema validator against the feature-tree part schema.

Issues are returned as data (a list of SchemaIssue); an empty list means valid.
"""

from ncad.spec.schema_validator import SchemaValidator


def _valid_document() -> dict:
    return {
        "schema_version": 2,
        "units": "mm",
        "parts": {
            "block": {
                "profile": "solid",
                "features": [
                    {
                        "id": "sk",
                        "op": "sketch",
                        "plane": "XY",
                        "elements": [
                            {"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}
                        ],
                    },
                    {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
                ],
            }
        },
    }


def test_valid_document_has_no_issues() -> None:
    assert SchemaValidator().validate(_valid_document()) == []


def test_missing_units_is_flagged() -> None:
    doc = _valid_document()
    del doc["units"]

    issues = SchemaValidator().validate(doc)

    assert any(issue.location == "<root>" for issue in issues)


def test_feature_without_id_is_flagged() -> None:
    doc = _valid_document()
    del doc["parts"]["block"]["features"][0]["id"]

    issues = SchemaValidator().validate(doc)

    assert issues != []


def test_negative_extrude_distance_is_flagged() -> None:
    doc = _valid_document()
    doc["parts"]["block"]["features"][1]["distance"] = -8.0

    issues = SchemaValidator().validate(doc)

    assert issues != []


def test_selector_string_edges_is_valid() -> None:
    doc = {"schema_version": 1, "units": "mm", "parts": {"p": {
        "profile": "solid", "features": [
            {"id": "rnd", "op": "fillet", "radius": 1,
             "edges": "select edges where created_by='pad'"}]}}}
    assert SchemaValidator().validate(doc) == []


def test_hole_on_field_is_valid() -> None:
    doc = {"schema_version": 1, "units": "mm", "parts": {"p": {
        "profile": "solid", "features": [
            {"id": "h", "op": "hole", "diameter": 4, "depth": 5,
             "positions": [[1, 1]], "on": "pad.cap(+Z)"}]}}}
    assert SchemaValidator().validate(doc) == []
