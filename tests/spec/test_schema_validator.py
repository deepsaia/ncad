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
    spec["roof"]["kind"] = "vault"  # not in the roof kind enum

    issues = SchemaValidator().validate(spec)

    assert any("vault" in issue.message for issue in issues)


def test_gable_and_shed_roofs_validate() -> None:
    for kind in ("gable", "shed"):
        spec = _valid_spec()
        spec["roof"] = {"kind": kind, "pitch": 0.5, "ridge_axis": "x", "thickness": 0.2}

        assert SchemaValidator().validate(spec) == [], f"{kind} roof should validate"


def test_hip_roof_validates() -> None:
    spec = _valid_spec()
    spec["roof"] = {"kind": "hip", "pitch": 0.5}

    assert SchemaValidator().validate(spec) == []


def test_invalid_ridge_axis_is_reported() -> None:
    spec = _valid_spec()
    spec["roof"] = {"kind": "gable", "ridge_axis": "z"}

    issues = SchemaValidator().validate(spec)

    assert any("ridge_axis" in issue.location for issue in issues)


def test_plain_footprint_polygon_validates() -> None:
    spec = _valid_spec()
    spec["storeys"][0]["footprint"] = [[0, 0], [6, 0], [6, 4], [0, 4]]

    assert SchemaValidator().validate(spec) == []


def test_footprint_with_corner_radius_vertex_validates() -> None:
    spec = _valid_spec()
    # Mixed: plain points and an object vertex carrying a corner radius.
    spec["storeys"][0]["footprint"] = [
        [0, 0],
        [6, 0],
        {"point": [6, 4], "corner_radius": 1.0},
        [0, 4],
    ]

    assert SchemaValidator().validate(spec) == []


def test_negative_corner_radius_is_reported() -> None:
    spec = _valid_spec()
    spec["storeys"][0]["footprint"] = [
        [0, 0],
        [6, 0],
        {"point": [6, 4], "corner_radius": -1.0},
        [0, 4],
    ]

    assert SchemaValidator().validate(spec) != []


def test_arc_wall_form_validates() -> None:
    spec = _valid_spec()
    spec["storeys"][0]["walls"].append(
        {
            "id": "arc_0",
            "start": [6.0, 0.0],
            "end": [6.0, 4.0],
            "thickness": 0.2,
            "arc": {"center": [4.0, 2.0], "clockwise": False},
        }
    )

    assert SchemaValidator().validate(spec) == []


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
