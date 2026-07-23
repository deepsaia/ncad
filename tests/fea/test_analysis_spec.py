import pytest

from ncad.fea.analysis_params import AnalysisParamError
from ncad.fea.analysis_spec import AnalysisSpec, AnalysisSpecError


def _doc(**over):
    base = {
        "analysis": {
            "part": "bracket.hocon",
            "mesh": {"element_size": 3.0, "order": 2},
            "constraints": [{"name": "root", "where": {"face": "bottom"}, "type": "encastre"}],
            "loads": [{"name": "tip", "where": {"face": "top"}, "type": "pressure",
                       "magnitude": 2.5e5}],
            "steps": [{"name": "stress", "procedure": "static"}],
        }
    }
    base["analysis"].update(over)
    return base


def test_parses_part_and_mesh():
    spec = AnalysisSpec(_doc())
    assert spec.part == "bracket.hocon"
    assert spec.mesh["element_size"] == 3.0 and spec.mesh["order"] == 2


def test_mesh_defaults_order_two_when_absent():
    spec = AnalysisSpec(_doc(mesh={"element_size": 5.0}))
    assert spec.mesh["order"] == 2


def test_normalizes_constraints_and_loads_and_steps():
    spec = AnalysisSpec(_doc())
    assert spec.constraints[0]["dof"] == [1, 2, 3, 4, 5, 6]
    assert spec.loads[0]["magnitude"] == 2.5e5
    assert spec.steps[0]["procedure"] == "static"


def test_missing_analysis_block_raises():
    with pytest.raises(AnalysisSpecError):
        AnalysisSpec({"part": "x"})


def test_missing_part_raises():
    doc = _doc()
    del doc["analysis"]["part"]
    with pytest.raises(AnalysisSpecError):
        AnalysisSpec(doc)


def test_bad_constraint_propagates_as_param_error():
    with pytest.raises(AnalysisParamError):
        AnalysisSpec(_doc(constraints=[{"where": {"face": "top"}, "type": "encastre"}]))


def test_material_override_defaults_none():
    assert AnalysisSpec(_doc()).material_override is None
    spec = AnalysisSpec(_doc(material={"structural": {"youngs_modulus": 1.0}}))
    assert spec.material_override == {"structural": {"youngs_modulus": 1.0}}
