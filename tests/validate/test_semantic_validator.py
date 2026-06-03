"""Tests for the semantic validators.

These check meaning the schema can't: openings fitting their walls, rooms reachable via
doors, architectural minimums. Issues are returned as data (list of Issue), tagged with
the offending entity ids. A clean spec yields no issues. See design.md §5.
"""

from ncad.generate.generator import Generator
from ncad.validate.semantic_validator import SemanticValidator


def _clean_spec() -> dict:
    return Generator({"width": 12.0, "depth": 9.0, "num_rooms": 4}).generate(seed=42)


def test_generated_spec_has_no_semantic_issues() -> None:
    issues = SemanticValidator().validate(_clean_spec())

    assert issues == [], f"unexpected issues: {[i.message for i in issues]}"


def test_opening_wider_than_wall_is_flagged() -> None:
    spec = _clean_spec()
    wall = spec["storeys"][0]["walls"][0]
    wall["openings"] = [
        {"id": "huge", "kind": "window", "along": 0.5, "width": 999.0, "height": 1.0, "sill": 0.5}
    ]

    issues = SemanticValidator().validate(spec)

    assert any(i.entity_id == "huge" for i in issues)


def test_opening_taller_than_wall_is_flagged() -> None:
    spec = _clean_spec()
    wall = spec["storeys"][0]["walls"][0]
    wall["openings"] = [
        {"id": "tall", "kind": "window", "along": 0.5, "width": 0.5, "height": 99.0, "sill": 0.5}
    ]

    issues = SemanticValidator().validate(spec)

    assert any(i.entity_id == "tall" for i in issues)


def test_overlapping_openings_on_same_wall_flagged() -> None:
    spec = _clean_spec()
    wall = spec["storeys"][0]["walls"][0]
    wall["openings"] = [
        {"id": "a", "kind": "window", "along": 0.5, "width": 1.0, "height": 1.0, "sill": 0.9},
        {"id": "b", "kind": "window", "along": 0.51, "width": 1.0, "height": 1.0, "sill": 0.9},
    ]

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "opening_overlap" for i in issues)


def test_unreachable_room_is_flagged() -> None:
    spec = _clean_spec()
    # Strip all doors so no room is reachable from the others.
    for wall in spec["storeys"][0]["walls"]:
        wall["openings"] = [o for o in wall.get("openings", []) if o["kind"] != "door"]

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "unreachable_room" for i in issues)


def test_tiny_room_below_min_area_flagged() -> None:
    spec = _clean_spec()
    spec["storeys"][0]["rooms"][0]["polygon"] = [[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]]

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "min_room_area" for i in issues)


def test_low_ceiling_flagged() -> None:
    spec = _clean_spec()
    spec["storeys"][0]["height"] = 1.5

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "min_ceiling_height" for i in issues)


def test_issues_carry_entity_ids() -> None:
    spec = _clean_spec()
    spec["storeys"][0]["walls"][0]["openings"] = [
        {"id": "bad", "kind": "door", "along": 0.99, "width": 5.0, "height": 2.1, "sill": 0.0}
    ]

    issues = SemanticValidator().validate(spec)

    assert all(isinstance(i.entity_id, str) for i in issues)
    assert any(i.entity_id == "bad" for i in issues)


def test_open_exterior_loop_is_flagged() -> None:
    # Break the perimeter: shorten one exterior wall so its end no longer meets the next.
    spec = _clean_spec()
    spec["storeys"][0]["walls"][0]["end"] = [11.0, 0.0]  # was the corner; now a gap

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "open_wall_loop" for i in issues)


def test_irregular_closed_loop_passes(tmp_path) -> None:
    from pathlib import Path

    from ncad.spec.spec_loader import SpecLoader

    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    spec = SpecLoader().load(str(fixtures / "irregular_house.hocon"))

    issues = SemanticValidator().validate(spec)

    assert not any(i.kind == "open_wall_loop" for i in issues)
