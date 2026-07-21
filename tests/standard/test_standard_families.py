"""The pipe/flange/gasket/bearing/i_beam families generate docs by designation + custom dims."""

import pytest

from ncad.standard import StandardLibrary
from ncad.standard.bolt_circle import bolt_circle_positions


def test_all_families_registered():
    families = set(StandardLibrary().families())
    assert families == {"washer", "hex_nut", "pipe", "flange", "gasket", "bearing", "i_beam",
                        "pipe_fitting"}


def test_pipe_bore_from_wall():
    doc = StandardLibrary().generate("pipe", "DN50")
    features = doc["parts"]["pipe_dn50"]["features"]
    outer = next(f for f in features if f["id"] == "outer")
    bore = next(f for f in features if f["id"] == "bore")
    # DN50: OD 60.3, wall 3.6 -> bore 60.3 - 2*3.6.
    assert outer["d"] == pytest.approx(60.3)
    assert bore["d"] == pytest.approx(60.3 - 2 * 3.6)


def test_pipe_length_falls_back_to_table_default():
    doc = StandardLibrary().generate("pipe", "DN50")
    outer = doc["parts"]["pipe_dn50"]["features"][0]
    assert outer["h"] == pytest.approx(300)  # length_default for DN50


def test_flange_drills_full_bolt_circle():
    doc = StandardLibrary().generate("flange", "NPS4")
    bolts = next(f for f in doc["parts"]["flange_nps4"]["features"] if f["id"] == "bolts")
    assert len(bolts["positions"]) == 8  # NPS4 class 150 = 8 bolts
    assert bolts["diameter"] == pytest.approx(19.1)


def test_bearing_is_a_bored_ring():
    doc = StandardLibrary().generate("bearing", "6205")
    ops = [f["op"] for f in doc["parts"]["bearing_6205"]["features"]]
    assert ops == ["primitive", "primitive", "boolean"]


def test_i_beam_section_has_twelve_points():
    doc = StandardLibrary().generate("i_beam", "IPE200")
    section = doc["parts"]["i_beam_ipe200"]["features"][0]["elements"][0]
    assert len(section["points"]) == 12


def test_custom_pipe_dimensions():
    doc = StandardLibrary().generate_custom(
        "pipe", {"outer_diameter": 50.0, "wall_thickness": 5.0, "length": 100.0})
    outer = doc["parts"]["pipe_custom"]["features"][0]
    assert outer["d"] == pytest.approx(50.0)
    assert outer["h"] == pytest.approx(100.0)


def test_custom_flange_missing_dimension_raises():
    with pytest.raises(ValueError, match="missing"):
        StandardLibrary().generate_custom("flange", {"outer_diameter": 120.0})


def test_bolt_circle_positions_evenly_spaced():
    positions = bolt_circle_positions(100.0, 4)
    assert len(positions) == 4
    # First hole on +X at radius 50; the four lie on the circle.
    assert positions[0] == pytest.approx([50.0, 0.0])
    for x, y in positions:
        assert (x ** 2 + y ** 2) ** 0.5 == pytest.approx(50.0)


def test_bolt_circle_rejects_nonpositive_count():
    with pytest.raises(ValueError, match="bolt count must be positive"):
        bolt_circle_positions(100.0, 0)
