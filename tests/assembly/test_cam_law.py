import math

import pytest

from ncad.assembly.cam_law import CamLaw, CamLawError


def test_harmonic_lift_rises_and_returns():
    # harmonic single lobe: lift/2 * (1 - cos(theta)); 0 at 0, peak `lift` at 180, 0 at 360.
    law = CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    assert math.isclose(law.lift(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(law.lift(180.0), 12.0, abs_tol=1e-9)
    assert math.isclose(law.lift(360.0), 0.0, abs_tol=1e-9)
    assert math.isclose(law.lift(90.0), 6.0, abs_tol=1e-9)   # lift/2 at quarter


def test_harmonic_two_lobes_peaks_twice():
    law = CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 10, "lobes": 2})
    assert math.isclose(law.lift(90.0), 10.0, abs_tol=1e-9)   # first peak at 360/2/2 = 90
    assert math.isclose(law.lift(180.0), 0.0, abs_tol=1e-9)   # valley at 180
    assert math.isclose(law.lift(270.0), 10.0, abs_tol=1e-9)  # second peak


def test_sine_law_rises_and_returns():
    # sine: lift * sin(lobes*theta/2)^2; same 0->lift->0 shape, single lobe.
    law = CamLaw.from_profile({"law": "sine", "base_r": 15, "lift": 8, "lobes": 1})
    assert math.isclose(law.lift(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(law.lift(180.0), 8.0, abs_tol=1e-9)
    assert math.isclose(law.lift(360.0), 0.0, abs_tol=1e-9)


def test_lift_is_never_negative():
    law = CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 3})
    for deg in range(0, 361, 5):
        assert law.lift(float(deg)) >= -1e-12


def test_polar_radius_is_base_plus_lift():
    law = CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    assert math.isclose(law.radius(0.0), 20.0, abs_tol=1e-9)
    assert math.isclose(law.radius(180.0), 32.0, abs_tol=1e-9)


def test_expression_is_smooth_time_function():
    # The follower motion is a function of `time` (metres) over t 0..1; a smooth expression only
    # (no min/max/conditionals, which OndselSolver rejects).
    law = CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    expr = law.expression(a0_deg=0.0, span_deg=360.0)
    assert isinstance(expr, str)
    for token in ("min", "max", "abs", ">", "<", "if"):
        assert token not in expr
    # It is expressed in metres (mm/1000) for the ASMT translational motion; peak 12 mm -> 0.012.
    assert "time" in expr


def test_bad_law_raises():
    with pytest.raises(CamLawError, match="law"):
        CamLaw.from_profile({"law": "dwell", "base_r": 20, "lift": 12, "lobes": 1})


def test_bad_params_raise():
    with pytest.raises(CamLawError):
        CamLaw.from_profile({"law": "harmonic", "base_r": -1, "lift": 12, "lobes": 1})
    with pytest.raises(CamLawError):
        CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 0, "lobes": 1})
    with pytest.raises(CamLawError):
        CamLaw.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 0})
