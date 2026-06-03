"""Tests for SpecCompiler: a coarse, agent-authorable brief -> a precise building spec.

The brief uses only round-number coordinates and corner indices — the level of precision
an LLM agent can emit. The compiler expands it (tangent points, arc centers, walls,
rooms) into a schema-valid, semantically-clean spec the builder consumes.
"""

import pytest

from ncad.compile.spec_compiler import SpecCompiler
from ncad.spec.schema_validator import SchemaValidator
from ncad.validate.semantic_validator import SemanticValidator


def _brief() -> dict:
    # Round numbers an agent could plausibly produce: a 10x8 rectangle, two corners
    # rounded, four rooms, flat roof.
    return {
        "footprint": [[0, 0], [10, 0], [10, 8], [0, 8]],
        "rounded_corners": {"1": 1.5, "3": 1.0},
        "num_rooms": 4,
        "storey_height": 3.0,
        "roof": "flat",
    }


def test_compiles_to_schema_valid_spec() -> None:
    spec = SpecCompiler().compile(_brief())

    assert SchemaValidator().validate(spec) == []


def test_compiled_spec_is_semantically_clean() -> None:
    spec = SpecCompiler().compile(_brief())

    issues = SemanticValidator().validate(spec)
    assert issues == [], f"unexpected: {[(i.kind, i.entity_id) for i in issues]}"


def test_rounded_corners_become_arc_walls() -> None:
    spec = SpecCompiler().compile(_brief())

    arc_walls = [w for w in spec["storeys"][0]["walls"] if "arc" in w]
    assert len(arc_walls) == 2  # the two requested rounded corners


def test_footprint_marks_only_requested_corners_rounded() -> None:
    spec = SpecCompiler().compile(_brief())

    footprint = spec["storeys"][0]["footprint"]
    rounded = [v for v in footprint if isinstance(v, dict)]
    assert len(rounded) == 2


def test_no_rounded_corners_is_all_sharp() -> None:
    brief = _brief()
    brief["rounded_corners"] = {}

    spec = SpecCompiler().compile(brief)

    assert all(isinstance(v, list) for v in spec["storeys"][0]["footprint"])
    assert not any("arc" in w for w in spec["storeys"][0]["walls"])


def test_irregular_polygon_compiles() -> None:
    # Arbitrary coarse hexagon with one rounded corner — round numbers only.
    brief = {
        "footprint": [[0, 0], [12, 0], [12, 6], [8, 10], [0, 10]],
        "rounded_corners": {"3": 2.0},
        "num_rooms": 3,
        "storey_height": 3.0,
        "roof": "flat",
    }

    spec = SpecCompiler().compile(brief)

    assert SchemaValidator().validate(spec) == []
    assert SemanticValidator().validate(spec) == []


def test_is_deterministic() -> None:
    a = SpecCompiler().compile(_brief())
    b = SpecCompiler().compile(_brief())

    assert a == b


def test_default_is_single_storey() -> None:
    spec = SpecCompiler().compile(_brief())

    assert len(spec["storeys"]) == 1
    assert spec["storeys"][0]["elevation"] == 0.0


def test_balcony_adds_paired_opening_and_entry() -> None:
    brief = {**_brief(), "num_storeys": 2,
             "balconies": [{"storey": 1, "wall": 0, "along": 0.5, "length": 3.0, "depth": 1.5}]}

    spec = SpecCompiler().compile(brief)

    upper = spec["storeys"][1]
    assert len(upper["balconies"]) == 1
    bwall_id = upper["balconies"][0]["wall_id"]
    wall = next(w for w in upper["walls"] if w["id"] == bwall_id)
    door = next(o for o in wall["openings"] if o["id"].endswith("_balcony_door"))
    assert door["width"] == 3.0  # = balcony length
    assert door["height"] == pytest.approx(0.9 * 3.0)  # 0.9 * storey height
    # The whole thing still validates.
    assert SchemaValidator().validate(spec) == []
    assert SemanticValidator().validate(spec) == []


def test_balcony_on_ground_floor_rejected() -> None:
    brief = {**_brief(), "num_storeys": 2,
             "balconies": [{"storey": 0, "wall": 0, "along": 0.5, "length": 3.0, "depth": 1.5}]}

    with pytest.raises(ValueError, match="ground floor"):
        SpecCompiler().compile(brief)


def test_no_balconies_compiles_unchanged() -> None:
    # A brief without balconies must not gain a balconies key anywhere.
    spec = SpecCompiler().compile({**_brief(), "num_storeys": 2})

    assert all("balconies" not in s for s in spec["storeys"])


def test_num_storeys_stacks_floors() -> None:
    brief = _brief()
    brief["num_storeys"] = 3

    spec = SpecCompiler().compile(brief)

    storeys = spec["storeys"]
    assert len(storeys) == 3
    assert [s["elevation"] for s in storeys] == [0.0, 3.0, 6.0]
    # Each storey has its own wall dicts (no aliasing).
    assert storeys[0]["walls"] is not storeys[1]["walls"]
    assert SchemaValidator().validate(spec) == []
    assert SemanticValidator().validate(spec) == []
