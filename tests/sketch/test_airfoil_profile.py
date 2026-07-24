import os

import pytest

from ncad.sketch.airfoil_profile import AirfoilParamError, AirfoilProfile

_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_naca_scaled_to_chord():
    pts = AirfoilProfile().points({"naca": "0012", "chord": 200, "samples": 40})
    xs = [p[0] for p in pts]
    assert max(xs) == pytest.approx(200.0, abs=1e-3)   # chord scales the unit section
    assert min(xs) == pytest.approx(0.0, abs=1e-3)


def test_naca_returns_a_closed_loop():
    pts = AirfoilProfile().points({"naca": "2412", "chord": 100})
    assert len(pts) >= 3
    assert pts[0] == pytest.approx(pts[-1], abs=1e-6)   # loop closes


def test_dat_ingest_parses_the_fixture():
    pts = AirfoilProfile().points({"dat": "naca0012.dat", "chord": 150}, base_dir=_FIXTURES)
    assert len(pts) >= 3
    assert max(p[0] for p in pts) == pytest.approx(150.0, abs=1e-2)


def test_both_sources_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"naca": "0012", "dat": "x.dat", "chord": 100})


def test_neither_source_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"chord": 100})


def test_bad_chord_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"naca": "0012", "chord": 0})


def test_bad_naca_code_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"naca": "12", "chord": 100})


def test_dat_without_base_dir_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"dat": "naca0012.dat", "chord": 100})


def test_missing_dat_raises():
    with pytest.raises(AirfoilParamError):
        AirfoilProfile().points({"dat": "nope.dat", "chord": 100}, base_dir=_FIXTURES)
