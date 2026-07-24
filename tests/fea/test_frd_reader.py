import os

from ncad.fea.frd_reader import FrdReader

_FRD = os.path.join(os.path.dirname(__file__), "fixtures", "mini.frd")
_REAL_FRD = os.path.join(os.path.dirname(__file__), "fixtures", "bracket_real.frd")
_MODAL_FRD = os.path.join(os.path.dirname(__file__), "fixtures", "modal.frd")
_STEEL = {"structural": {"yield": 370e6}}


def test_reads_nodes_and_disp_and_stress():
    result = FrdReader().read(_FRD, _STEEL)
    assert len(result["nodes"]) == 4
    assert result["summary"]["max_displacement"] > 0
    assert result["summary"]["max_von_mises"] > 0


def test_safety_factor_is_yield_over_max_von_mises():
    result = FrdReader().read(_FRD, _STEEL)
    sf = result["summary"]["safety_factor"]
    assert abs(sf - 370e6 / result["summary"]["max_von_mises"]) < 1e-6


def test_von_mises_of_uniaxial_stress_equals_that_stress():
    # The fixture's node 1 has SXX=100e6, all other components 0 -> von Mises = 100e6.
    result = FrdReader().read(_FRD, _STEEL)
    assert abs(result["summary"]["max_von_mises"] - 100e6) < 1.0


def test_max_displacement_is_largest_magnitude():
    # Node 4 has displacement (0, 0, 3e-3) -> magnitude 3e-3, the largest in the fixture.
    result = FrdReader().read(_FRD, _STEEL)
    assert abs(result["summary"]["max_displacement"] - 3e-3) < 1e-9


def test_reads_real_frd_with_run_together_columns():
    # Real ccx .frd packs negative values with no separating space (e.g. '1-4.00000E+01'), so the
    # reader must parse fixed 12-char columns, not split on whitespace. This fixture is real-format.
    result = FrdReader().read(_REAL_FRD, _STEEL)
    assert len(result["nodes"]) == 3
    # Node 1 sits at x=-40 (run-together with the node number in the coord block).
    assert result["nodes"][1][0] == -40.0
    # Node 1 has SXX=100e6, rest 0 -> von Mises = 100e6 (the max in the fixture).
    assert abs(result["summary"]["max_von_mises"] - 100e6) < 1.0


def test_frequency_modes_do_not_corrupt_static_result():
    # A chained static+frequency solve appends mass-normalized eigenVECTOR DISP/STRESS blocks
    # (arbitrary magnitude: 88 GPa, 200 GPa here) after the static result, sharing the same field
    # names. The reader must keep the STATIC result (100e6 von Mises, 3e-3 displacement), NOT let a
    # modal block overwrite it. Regression for the wing that read 88 GPa off a mode shape.
    result = FrdReader().read(_MODAL_FRD, _STEEL)
    assert abs(result["summary"]["max_von_mises"] - 100e6) < 1.0
    assert abs(result["summary"]["max_displacement"] - 3e-3) < 1e-9


def test_eigenfrequencies_are_collected_once_per_mode():
    # The modal fixture has two modes (KEY 102 at 62.7 Hz, KEY 103 at 285.5 Hz), each written as a
    # DISP + a STRESS block. The reader collects each mode's frequency ONCE (dedup by mode key).
    result = FrdReader().read(_MODAL_FRD, _STEEL)
    freqs = result["summary"]["frequencies"]
    assert len(freqs) == 2
    assert abs(freqs[0] - 62.72320333) < 1e-6
    assert abs(freqs[1] - 285.4686974) < 1e-6


def test_static_only_frd_has_no_frequencies():
    # A pure static result carries no modal blocks, so frequencies is empty (not None).
    result = FrdReader().read(_FRD, _STEEL)
    assert result["summary"]["frequencies"] == []


def test_write_vtk_emits_a_field_mesh(tmp_path):
    import pytest
    pytest.importorskip("meshio")
    result = FrdReader().read(_FRD, _STEEL)
    out = str(tmp_path / "mini.analysis.vtk")
    # One tetra over the fixture's 4 nodes (frd node ids 1..4).
    FrdReader().write_vtk(result, [[1, 2, 3, 4]], out)
    text = open(out).read()
    assert os.path.getsize(out) > 0
    assert "von_mises" in text and "displacement" in text
