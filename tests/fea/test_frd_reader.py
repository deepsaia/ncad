import os

from ncad.fea.frd_reader import FrdReader

_FRD = os.path.join(os.path.dirname(__file__), "fixtures", "mini.frd")
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
