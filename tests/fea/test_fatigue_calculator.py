import pytest

from ncad.fea.analysis_error import AnalysisError
from ncad.fea.fatigue_calculator import FatigueCalculator

# A representative steel S-N set (matches the seed values added in Task 4).
_STEEL = {"structural": {"ultimate": 440e6, "endurance_limit": 220e6,
                         "fatigue_strength_coeff": 1200e6, "fatigue_exponent": -0.085}}


def test_below_endurance_limit_is_infinite_life():
    # Fully reversed (R=-1), peak 300e6 -> alternating 150e6 < endurance 220e6 -> infinite.
    out = FatigueCalculator().life(300e6, -1.0, _STEEL)
    assert out["infinite_life"] is True
    assert out["cycles_to_failure"] is None
    assert out["alternating_stress"] == pytest.approx(150e6)
    assert out["mean_stress"] == pytest.approx(0.0)


def test_above_endurance_limit_gives_finite_basquin_life():
    # Fully reversed peak 600e6 -> alternating 300e6 > endurance
    # -> finite N = (300e6/1200e6)^(1/-0.085).
    out = FatigueCalculator().life(600e6, -1.0, _STEEL)
    assert out["infinite_life"] is False
    expected = (300e6 / 1200e6) ** (1.0 / -0.085)
    assert out["cycles_to_failure"] == pytest.approx(expected, rel=1e-6)


def test_mean_stress_reduces_life_via_goodman():
    # Same peak, R=-1 (zero mean) vs R=0 (nonzero mean): the mean stress shortens life.
    reversed_life = FatigueCalculator().life(600e6, -1.0, _STEEL)["cycles_to_failure"]
    pulsating_life = FatigueCalculator().life(600e6, 0.0, _STEEL)["cycles_to_failure"]
    assert pulsating_life < reversed_life


def test_safety_factor_is_endurance_over_alternating():
    out = FatigueCalculator().life(300e6, -1.0, _STEEL)
    assert out["fatigue_safety_factor"] == pytest.approx(220e6 / 150e6, rel=1e-6)


def test_zero_peak_is_infinite_life():
    out = FatigueCalculator().life(0.0, -1.0, _STEEL)
    assert out["infinite_life"] is True and out["cycles_to_failure"] is None


def test_missing_sn_data_raises():
    with pytest.raises(AnalysisError):
        FatigueCalculator().life(300e6, -1.0, {"structural": {"yield": 370e6}})


def test_mean_at_or_above_ultimate_raises():
    # R close to 1 pushes the mean toward sigma_max; a mean >= ultimate
    # is static yield, not fatigue.
    with pytest.raises(AnalysisError):
        FatigueCalculator().life(500e6, 0.95, _STEEL)
