"""StandardLibrary generates part documents by designation and by custom dimensions."""

import math

import pytest

from ncad.standard import StandardLibrary


def test_families_and_designations():
    lib = StandardLibrary()
    # washer + hex_nut are the S5 originals; the family set grows as new families register.
    assert {"washer", "hex_nut"} <= set(lib.families())
    assert "M8" in lib.designations("washer")
    assert "M8" in lib.designations("hex_nut")


def test_generate_washer_by_designation_shape():
    doc = StandardLibrary().generate("washer", "M8")
    assert doc["units"] == "mm"
    part = doc["parts"]["washer_m8"]
    ops = [f["op"] for f in part["features"]]
    assert ops == ["sketch", "revolve"]
    # The revolved section spans inner->outer radius (ISO 7089 M8: id 8.4, od 16).
    rect = part["features"][0]["elements"][0]
    assert rect["w"] == pytest.approx((16.0 - 8.4) / 2.0)
    assert rect["h"] == pytest.approx(1.6)


def test_generate_hex_nut_by_designation_circumradius():
    doc = StandardLibrary().generate("hex_nut", "M8")
    part = doc["parts"]["hex_nut_m8"]
    assert [f["op"] for f in part["features"]] == [
        "sketch", "extrude", "sketch", "extrude", "boolean"]
    hexagon = part["features"][0]["elements"][0]
    assert hexagon["sides"] == 6
    # width across flats 13 -> circumradius = (13/2)/cos(30deg).
    assert hexagon["r"] == pytest.approx((13.0 / 2.0) / math.cos(math.pi / 6.0))
    bore = part["features"][2]["elements"][0]
    assert bore["d"] == pytest.approx(8.0)


def test_generate_custom_dimensions_bypasses_table():
    doc = StandardLibrary().generate_custom(
        "washer", {"inner_diameter": 5.0, "outer_diameter": 14.0, "thickness": 1.2})
    rect = doc["parts"]["washer_custom"]["features"][0]["elements"][0]
    assert rect["w"] == pytest.approx((14.0 - 5.0) / 2.0)
    assert rect["h"] == pytest.approx(1.2)


def test_custom_missing_dimension_raises():
    with pytest.raises(ValueError, match="missing"):
        StandardLibrary().generate_custom("hex_nut", {"thread_diameter": 8.0})


def test_unknown_family_raises():
    with pytest.raises(KeyError, match="unknown standard-part family"):
        StandardLibrary().generate("bolt", "M8")


def test_unknown_designation_raises():
    with pytest.raises(KeyError, match="unknown"):
        StandardLibrary().generate("washer", "M99")


def test_provenance_carries_standard_and_version():
    prov = StandardLibrary().provenance("hex_nut")
    assert prov["standard"] == "ISO 4032"
    assert prov["version"] and prov["source"]
