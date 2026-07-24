import pytest

from ncad.sketch.airfoil_profile import AirfoilParamError
from ncad.sketch.entity_expander import EntityExpander


def test_airfoil_expands_to_one_interpolated_spline():
    entities = [{"id": "wing", "type": "airfoil", "naca": "2412", "chord": 100, "samples": 30}]
    out = EntityExpander().expand(entities)
    splines = [e for e in out if e["type"] == "interpolated"]
    points = [e for e in out if e["type"] == "point"]
    assert len(splines) == 1
    assert len(points) >= 3
    # The spline references the emitted point ids in order.
    assert splines[0]["points"] == [p["id"] for p in points]
    assert all(pid.startswith("wing/") for pid in splines[0]["points"])


def test_airfoil_points_are_fixed_and_deterministic():
    entities = [{"id": "w", "type": "airfoil", "naca": "0012", "chord": 50, "samples": 20}]
    a = EntityExpander().expand(entities)
    b = EntityExpander().expand(entities)
    assert a == b
    assert all(e.get("fixed") for e in a if e["type"] == "point")


def test_at_offsets_the_section():
    entities = [{"id": "w", "type": "airfoil", "naca": "0012", "chord": 100, "at": [10, 20]}]
    out = EntityExpander().expand(entities)
    xs = [e["at"][0] for e in out if e["type"] == "point"]
    ys = [e["at"][1] for e in out if e["type"] == "point"]
    assert min(xs) == pytest.approx(10.0, abs=1e-3)   # leading edge shifted by at.x
    assert min(ys) < 20.0 and max(ys) > 20.0          # section straddles at.y


def test_bad_airfoil_raises_a_clear_error():
    # Sugar entities that cannot produce valid geometry raise (as gear/geneva do); a bad airfoil
    # (no source) raises AirfoilParamError out of expand.
    entities = [{"id": "w", "type": "airfoil", "chord": 100}]
    with pytest.raises(AirfoilParamError):
        EntityExpander().expand(entities)
