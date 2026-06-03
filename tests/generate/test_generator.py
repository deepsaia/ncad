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


# --- rounded corners (opt-in via corner_radius) ---

_ROUNDED_L = {**_L_PARAMS, "corner_radius": 1.0}


def test_corner_radius_default_zero_keeps_plain_footprint() -> None:
    # Default (no corner_radius) must emit plain [x,y] footprint vertices — goldens frozen.
    spec = Generator(_L_PARAMS).generate(seed=42)

    assert all(isinstance(v, list) for v in spec["storeys"][0]["footprint"])


@pytest.mark.parametrize("shape", ["L", "T", "U"])
def test_rounded_shapes_are_valid_and_round_trip(shape: str) -> None:
    spec = Generator({**_PARAMS, "footprint_shape": shape, "corner_radius": 1.0}).generate(seed=42)

    assert SchemaValidator().validate(spec) == [], f"{shape} schema"
    assert SemanticValidator().validate(spec) == [], f"{shape} semantic"
    arc_walls = [w for w in spec["storeys"][0]["walls"] if "arc" in w]
    assert arc_walls, f"{shape} should have arc walls"


@pytest.mark.parametrize("shape", ["L", "T", "U"])
def test_rounded_shapes_round_both_convex_and_concave(shape: str) -> None:
    # Every shape has both convex (outer) and concave (notch) corners; both must round.
    spec = Generator({**_PARAMS, "footprint_shape": shape, "corner_radius": 1.0}).generate(seed=42)

    arcs = [w["arc"] for w in spec["storeys"][0]["walls"] if "arc" in w]
    assert any(a["clockwise"] for a in arcs), f"{shape} missing concave (cw) arc"
    assert any(not a["clockwise"] for a in arcs), f"{shape} missing convex (ccw) arc"


def test_rounded_l_emits_object_footprint_vertices() -> None:
    spec = Generator(_ROUNDED_L).generate(seed=42)

    footprint = spec["storeys"][0]["footprint"]
    rounded = [v for v in footprint if isinstance(v, dict) and v.get("corner_radius", 0) > 0]
    assert rounded, "expected at least one rounded (object-form) vertex"


def test_rounded_l_has_arc_walls() -> None:
    spec = Generator(_ROUNDED_L).generate(seed=42)

    arc_walls = [w for w in spec["storeys"][0]["walls"] if "arc" in w]
    assert arc_walls, "expected at least one arc wall at a rounded corner"


def test_rounded_l_is_deterministic() -> None:
    a = Generator(_ROUNDED_L).generate(seed=42)
    b = Generator(_ROUNDED_L).generate(seed=42)

    assert a == b
