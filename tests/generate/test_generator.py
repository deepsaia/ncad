"""Tests for the Generator: (seed, params) -> schema-valid, deterministic spec."""

import pytest

from ncad.generate.generator import Generator
from ncad.spec.schema_validator import SchemaValidator
from ncad.validate.semantic_validator import SemanticValidator

_PARAMS = {"width": 12.0, "depth": 9.0, "num_rooms": 4, "storey_height": 3.0}


def test_generated_spec_is_schema_valid() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    issues = SchemaValidator().validate(spec)
    assert issues == [], f"generated spec has schema issues: {issues}"


def test_seed_is_recorded_in_spec() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    assert spec["seed"] == 42


def test_same_seed_and_params_produce_identical_spec() -> None:
    a = Generator(_PARAMS).generate(seed=42)
    b = Generator(_PARAMS).generate(seed=42)

    assert a == b


def test_different_seed_produces_different_spec() -> None:
    a = Generator(_PARAMS).generate(seed=1)
    b = Generator(_PARAMS).generate(seed=2)

    assert a != b


def test_room_count_matches_request() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    rooms = spec["storeys"][0]["rooms"]
    assert len(rooms) == 4


def test_has_four_exterior_walls_plus_interior_walls() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    walls = spec["storeys"][0]["walls"]
    # 4 exterior + (num_rooms - 1) interior
    assert len(walls) == 4 + (4 - 1)


def test_every_entity_has_a_unique_id() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    ids = []
    storey = spec["storeys"][0]
    for wall in storey["walls"]:
        ids.append(wall["id"])
        for opening in wall.get("openings", []):
            ids.append(opening["id"])
    for room in storey["rooms"]:
        ids.append(room["id"])

    assert len(ids) == len(set(ids)), "duplicate entity ids found"


def test_roof_is_flat() -> None:
    spec = Generator(_PARAMS).generate(seed=42)

    assert spec["roof"]["kind"] == "flat"


# --- L/T/U footprint shapes (opt-in via footprint_shape) ---

_L_PARAMS = {**_PARAMS, "footprint_shape": "L"}


def test_default_shape_is_rect_without_footprint_field() -> None:
    # The frozen rect path must not emit a footprint polygon (keeps golden byte-identical).
    spec = Generator(_PARAMS).generate(seed=42)

    assert "footprint" not in spec["storeys"][0]


@pytest.mark.parametrize("shape", ["L", "T", "U"])
def test_shaped_spec_is_schema_and_semantically_valid(shape: str) -> None:
    spec = Generator({**_PARAMS, "footprint_shape": shape}).generate(seed=42)

    assert SchemaValidator().validate(spec) == [], f"{shape} schema issues"
    assert SemanticValidator().validate(spec) == [], f"{shape} semantic issues"


def test_l_shape_emits_footprint_polygon() -> None:
    spec = Generator(_L_PARAMS).generate(seed=42)

    footprint = spec["storeys"][0]["footprint"]
    assert len(footprint) == 6  # L has six corners


def test_l_shape_walls_are_axis_aligned() -> None:
    spec = Generator(_L_PARAMS).generate(seed=42)

    for wall in spec["storeys"][0]["walls"]:
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        assert x0 == x1 or y0 == y1, f"wall {wall['id']} is not axis-aligned"


def test_l_shape_is_deterministic() -> None:
    a = Generator(_L_PARAMS).generate(seed=42)
    b = Generator(_L_PARAMS).generate(seed=42)

    assert a == b


def test_pitched_roof_on_shaped_footprint_raises() -> None:
    params = {**_L_PARAMS, "roof_kind": "gable"}

    with pytest.raises(ValueError, match="roof"):
        Generator(params).generate(seed=42)
