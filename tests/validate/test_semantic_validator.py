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


def _two_storey(upper_walls: list) -> dict:
    ground = {
        "elevation": 0.0,
        "height": 3.0,
        "walls": [{"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2,
                   "openings": [{"id": "front", "kind": "door", "along": 0.3, "width": 1.0,
                                 "height": 2.1, "sill": 0.0}]},
                  {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
                  {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
                  {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2}],
        "rooms": [{"id": "r", "polygon": [[0, 0], [8, 0], [8, 5], [0, 5]]}],
    }
    upper = {**ground, "elevation": 3.0, "walls": upper_walls}
    return {"schema_version": 1, "seed": 1, "units": "m",
            "storeys": [ground, upper], "roof": {"kind": "flat", "thickness": 0.2}}


def test_upper_exterior_door_without_balcony_is_flagged() -> None:
    # A door on an upper-floor exterior wall with no balcony has nothing to open onto.
    upper_walls = [
        {"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2,
         "openings": [{"id": "floating_door", "kind": "door", "along": 0.5, "width": 1.0,
                       "height": 2.1, "sill": 0.0}]},
        {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
        {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
        {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2},
    ]
    spec = _two_storey(upper_walls)

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "floating_exterior_door" and i.entity_id == "floating_door"
               for i in issues)


def test_upper_exterior_door_with_balcony_is_allowed() -> None:
    # The same door is fine when a balcony at that position gives it something to open onto.
    upper_walls = [
        {"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2,
         "openings": [{"id": "balcony_door", "kind": "door", "along": 0.5, "width": 3.0,
                       "height": 2.7, "sill": 0.0}]},
        {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
        {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
        {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2},
    ]
    spec = _two_storey(upper_walls)
    spec["storeys"][1]["balconies"] = [
        {"wall_id": "ext_0", "along": 0.5, "length": 3.0, "depth": 1.5}
    ]

    issues = SemanticValidator().validate(spec)

    assert not any(i.kind == "floating_exterior_door" for i in issues)


def test_ground_floor_exterior_door_is_allowed() -> None:
    # The ground-floor front door opens onto the ground — always fine.
    spec = _two_storey([
        {"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2},
        {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
        {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
        {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2},
    ])

    issues = SemanticValidator().validate(spec)

    assert not any(i.kind == "floating_exterior_door" for i in issues)


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


def test_opening_too_close_to_junction_is_flagged() -> None:
    # Two walls meeting at (6,0). A door at the far end of w1 hugs that shared corner,
    # where a window on the joined w2 would visually collide — flag it.
    spec = _clean_spec()
    storey = spec["storeys"][0]
    storey["walls"] = [
        {
            "id": "w1",
            "start": [0.0, 0.0],
            "end": [6.0, 0.0],
            "thickness": 0.2,
            "openings": [
                # along ~0.95 on a 6m wall → center at 5.7m, right edge at 6.2m: past the
                # junction at x=6, far too close to the corner shared with w2.
                {"id": "corner_door", "kind": "door", "along": 0.95, "width": 1.0,
                 "height": 2.1, "sill": 0.0},
            ],
        },
        {"id": "w2", "start": [6.0, 0.0], "end": [6.0, 4.0], "thickness": 0.2},
    ]
    storey["rooms"] = [{"id": "r0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}]

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "opening_near_junction" and i.entity_id == "corner_door"
               for i in issues)


def test_balcony_on_junction_is_flagged() -> None:
    # A balcony whose span runs into the wall's joined corner is geometrically invalid.
    spec = _two_storey([
        {"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2},
        {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
        {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
        {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2},
    ])
    # Balcony hugging the (8,0) corner: along ~0.95 on an 8m wall, 2m long → spills past the end.
    spec["storeys"][1]["balconies"] = [
        {"wall_id": "ext_0", "along": 0.95, "length": 2.0, "depth": 1.5}
    ]
    # Give it the paired door so it isn't flagged as floating instead.
    spec["storeys"][1]["walls"][0]["openings"] = [
        {"id": "bdoor", "kind": "door", "along": 0.95, "width": 2.0, "height": 2.5, "sill": 0.0}
    ]

    issues = SemanticValidator().validate(spec)

    assert any(i.kind == "balcony_near_junction" for i in issues)


def test_balcony_clear_of_junction_passes() -> None:
    spec = _two_storey([
        {"id": "ext_0", "start": [0, 0], "end": [8, 0], "thickness": 0.2},
        {"id": "ext_1", "start": [8, 0], "end": [8, 5], "thickness": 0.2},
        {"id": "ext_2", "start": [8, 5], "end": [0, 5], "thickness": 0.2},
        {"id": "ext_3", "start": [0, 5], "end": [0, 0], "thickness": 0.2},
    ])
    spec["storeys"][1]["balconies"] = [
        {"wall_id": "ext_0", "along": 0.5, "length": 3.0, "depth": 1.5}
    ]
    spec["storeys"][1]["walls"][0]["openings"] = [
        {"id": "bdoor", "kind": "door", "along": 0.5, "width": 3.0, "height": 2.5, "sill": 0.0}
    ]

    issues = SemanticValidator().validate(spec)

    assert not any(i.kind == "balcony_near_junction" for i in issues)


def test_opening_clear_of_junction_passes() -> None:
    # The same wall, but the door centered well away from both ends: no junction issue.
    spec = _clean_spec()
    storey = spec["storeys"][0]
    storey["walls"] = [
        {
            "id": "w1",
            "start": [0.0, 0.0],
            "end": [6.0, 0.0],
            "thickness": 0.2,
            "openings": [
                {"id": "mid_door", "kind": "door", "along": 0.5, "width": 1.0,
                 "height": 2.1, "sill": 0.0},
            ],
        },
        {"id": "w2", "start": [6.0, 0.0], "end": [6.0, 4.0], "thickness": 0.2},
    ]
    storey["rooms"] = [{"id": "r0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}]

    issues = SemanticValidator().validate(spec)

    assert not any(i.kind == "opening_near_junction" for i in issues)


def test_generated_specs_have_no_junction_issues() -> None:
    # The generator's placement guard must keep openings clear of junctions.
    for seed in (1, 7, 42, 99):
        issues = SemanticValidator().validate(
            Generator({"width": 14.0, "depth": 10.0, "num_rooms": 5}).generate(seed)
        )
        assert not any(i.kind == "opening_near_junction" for i in issues), f"seed {seed}"
