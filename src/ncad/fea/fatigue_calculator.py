"""High-cycle fatigue life from a solved static stress (Basquin S-N + Goodman mean correction).

Pure post-process, no solver: given the peak cyclic stress (sigma_max) and the cycle's stress ratio
R = sigma_min/sigma_max, the alternating and mean stresses follow; the Goodman rule corrects the
alternating stress to an equivalent fully-reversed stress against the material ultimate; the
Basquin S-N curve N = (sigma_ar / sigma_f')^(1/b) gives cycles-to-failure; below the endurance
limit the life is infinite. Material S-N data lives in the material's structural group. One class.
"""

import logging

from ncad.fea.analysis_error import AnalysisError

logger = logging.getLogger(__name__)

_SN_KEYS = ("ultimate", "endurance_limit", "fatigue_strength_coeff", "fatigue_exponent")


class FatigueCalculator:
    """Computes high-cycle fatigue life + safety from peak stress, stress ratio, and S-N data."""

    def life(self, peak_stress: float, ratio: float, material: dict) -> dict:
        """Return the fatigue result for ``peak_stress`` under stress ratio ``ratio``.

        :param peak_stress: the peak cyclic stress (sigma_max) in Pa.
        :param ratio: the stress ratio R = sigma_min / sigma_max.
        :param material: material dict with structural.ultimate/endurance_limit/fatigue_* S-N data.
        :raises AnalysisError: if the material lacks S-N data, or the mean stress reaches the
            ultimate (static yield, so a fatigue life is meaningless).
        """
        sn = _sn_data(material)
        sigma_max = float(peak_stress)
        if sigma_max <= 0.0:
            return _result(None, None, True, 0.0, 0.0)
        # sigma_a = sigma_max * (1 - R) / 2, sigma_m = sigma_max * (1 + R) / 2
        sigma_a = sigma_max * (1.0 - ratio) / 2.0
        sigma_m = sigma_max * (1.0 + ratio) / 2.0
        if sigma_m >= sn["ultimate"]:
            raise AnalysisError(
                f"fatigue mean stress {sigma_m:.3g} Pa reaches the ultimate "
                f"{sn['ultimate']:.3g} Pa (static yield); a fatigue life is not meaningful")
        # Goodman: the equivalent fully-reversed amplitude for a nonzero-mean cycle.
        sigma_ar = sigma_a / (1.0 - sigma_m / sn["ultimate"])
        safety = sn["endurance_limit"] / sigma_ar if sigma_ar > 0 else None
        if sigma_ar <= sn["endurance_limit"]:
            return _result(None, safety, True, sigma_a, sigma_m)
        # Basquin: N = (sigma_ar / sigma_f')^(1/b), b negative.
        cycles = (sigma_ar / sn["fatigue_strength_coeff"]) ** (1.0 / sn["fatigue_exponent"])
        logger.info("fatigue: peak %.3g Pa, R %.2f -> alt %.3g, N %.3g cycles",
                    sigma_max, ratio, sigma_ar, cycles)
        return _result(cycles, safety, False, sigma_a, sigma_m)


def _sn_data(material: dict) -> dict:
    """Extract the S-N constants from a material's structural group; raise if any are missing."""
    structural = material.get("structural") or {}
    missing = [k for k in _SN_KEYS if structural.get(k) is None]
    if missing:
        raise AnalysisError(
            f"fatigue needs material S-N data {list(_SN_KEYS)}; missing {missing}")
    return {k: float(structural[k]) for k in _SN_KEYS}


def _result(cycles: float | None, safety: float | None, infinite: bool,
            alternating: float, mean: float) -> dict:
    """Assemble the fatigue result dict."""
    return {"cycles_to_failure": cycles, "fatigue_safety_factor": safety,
            "infinite_life": infinite, "alternating_stress": alternating, "mean_stress": mean}
