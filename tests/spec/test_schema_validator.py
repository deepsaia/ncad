"""Tests for the schema validator: a loaded spec dict vs building_schema.hocon.

Validation issues are returned as data (a list of SchemaIssue), not raised — an empty
list means the spec is schema-valid. See design.md §5.
"""

from ncad.spec.schema_validator import SchemaValidator


def _valid_spec() -> dict:
    return {
        "schema_version": 1,
        "seed": 42,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [
                    {
                        "id": "wall_0",
                        "start": [0.0, 0.0],
                        "end": [6.0, 0.0],
                        "thickness": 0.2,
                    }
                ],
                "rooms": [
                    {"id": "room_0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}
                ],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_valid_spec_returns_no_issues() -> None:
    issues = SchemaValidator().validate(_valid_spec())

    assert issues == []


def test_missing_required_top_level_field_is_reported() -> None:
    spec = _valid_spec()
    del spec["roof"]

    issues = SchemaValidator().validate(spec)

    assert any("roof" in issue.message for issue in issues)


def test_wrong_schema_version_const_is_reported() -> None:
    spec = _valid_spec()
    spec["schema_version"] = 2

    issues = SchemaValidator().validate(spec)

    assert len(issues) >= 1


def test_unknown_roof_kind_is_reported() -> None:
    spec = _valid_spec()
    spec["roof"]["kind"] = "dome"

    issues = SchemaValidator().validate(spec)

    assert any("dome" in issue.message for issue in issues)


def test_issue_carries_location_path_into_nested_field() -> None:
    spec = _valid_spec()
    spec["storeys"][0]["walls"][0]["thickness"] = -1  # violates exclusiveMinimum

    issues = SchemaValidator().validate(spec)

    assert issues, "expected at least one issue"
    located = [i for i in issues if "thickness" in i.location]
    assert located, f"no issue located at thickness; got {[i.location for i in issues]}"


def test_opening_along_out_of_range_is_reported() -> None:
    spec = _valid_spec()
    spec["storeys"][0]["walls"][0]["openings"] = [
        {"id": "window_0", "kind": "window", "along": 1.5, "width": 1.2, "height": 1.4}
    ]

    issues = SchemaValidator().validate(spec)

    assert any("along" in i.location for i in issues)
