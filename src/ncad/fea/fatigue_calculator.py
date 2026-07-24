"""High-cycle fatigue life from a solved static stress (Basquin S-N + Goodman mean correction).

Pure post-process, no solver: given the static peak stress sigma_max and the cycle's stress ratio
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

        :raises AnalysisError: if the material lacks S-N data, or the mean stress reaches the
            ultimate (static yield, so a fatigue life is meaningless).
        """
        sn = _sn_data(material)
        stress_range = float(peak_stress)
        if stress_range <= 0.0:
            return _result(None, None, True, 0.0, 0.0)
        # stress_range = sigma_max - sigma_min, with sigma_min = R * sigma_max
        # so stress_range = sigma_max * (1 - R), thus sigma_max = stress_range / (1 - R)
        if ratio >= 1.0:
            # R >= 1 means sigma_min >= sigma_max, which is not a valid stress cycle
            raise AnalysisError(f"stress ratio R={ratio} >= 1 is not a valid cyclic load")
        sigma_max = stress_range / (1.0 - ratio)
        sigma_min = ratio * sigma_max
        alternating = (sigma_max - sigma_min) / 2.0
        mean = (sigma_max + sigma_min) / 2.0
        if mean >= sn["ultimate"]:
            raise AnalysisError(
                f"fatigue mean stress {mean:.3g} Pa reaches the ultimate {sn['ultimate']:.3g} Pa "
                f"(static yield); a fatigue life is not meaningful")
        # Goodman: the equivalent fully-reversed amplitude for a nonzero-mean cycle.
        equivalent = alternating / (1.0 - mean / sn["ultimate"])
        safety = sn["endurance_limit"] / equivalent if equivalent > 0 else None
        if equivalent <= sn["endurance_limit"]:
            return _result(None, safety, True, alternating, mean)
        # Basquin: N = (sigma_ar / sigma_f')^(1/b), b negative.
        cycles = (equivalent / sn["fatigue_strength_coeff"]) ** (1.0 / sn["fatigue_exponent"])
        logger.info("fatigue: range %.3g Pa, R %.2f -> alt %.3g, N %.3g cycles",
                    stress_range, ratio, equivalent, cycles)
        return _result(cycles, safety, False, alternating, mean)


def _sn_data(material: dict) -> dict:
    """Extract the S-N constants from a material's structural group; raise if any are missing."""
    structural = material.get("structural") or {}
    missing = [k for k in _SN_KEYS if structural.get(k) is None]
    if missing:
        raise AnalysisError(
            f"fatigue needs material S-N data {list(_SN_KEYS)}; missing {missing}")
    return {k: float(structural[k]) for k in _SN_KEYS}


def _result(cycles, safety, infinite: bool, alternating: float, mean: float) -> dict:
    """Assemble the fatigue result dict."""
    return {"cycles_to_failure": cycles, "fatigue_safety_factor": safety,
            "infinite_life": infinite, "alternating_stress": alternating, "mean_stress": mean}
