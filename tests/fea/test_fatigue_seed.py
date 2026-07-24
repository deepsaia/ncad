from ncad.fea.fatigue_calculator import FatigueCalculator
from ncad.spec.material_library import MaterialLibrary


def test_seed_metals_carry_sn_data_and_compute_life():
    lib = MaterialLibrary({})
    for name in ("steel_1018", "aluminium_6061", "steel_4140"):
        material = lib.resolve(name)
        sn = material["structural"]
        assert all(k in sn for k in
                   ("ultimate", "endurance_limit", "fatigue_strength_coeff", "fatigue_exponent"))
        # The S-N data produces a real fatigue result (no raise) at a moderate stress.
        out = FatigueCalculator().life(0.5 * sn["ultimate"], -1.0, material)
        assert "infinite_life" in out
