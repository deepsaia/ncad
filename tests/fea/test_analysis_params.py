import pytest

from ncad.fea.analysis_params import AnalysisParamError, validate_constraint


def test_encastre_fixes_all_six_dof():
    c = validate_constraint({"name": "root", "where": {"face": "bottom"}, "type": "encastre"})
    assert c["dof"] == [1, 2, 3, 4, 5, 6]
    assert c["value"] == 0.0
    assert c["name"] == "root"
    assert c["where"] == {"face": "bottom"}


def test_pinned_fixes_translations():
    c = validate_constraint({"name": "p", "where": {"face": "top"}, "type": "pinned"})
    assert c["dof"] == [1, 2, 3]


def test_explicit_dof_with_prescribed_value():
    c = validate_constraint(
        {"name": "d", "where": {"face": "top"}, "dof": [1, 2], "value": 0.5})
    assert c["dof"] == [1, 2] and c["value"] == 0.5


def test_missing_name_raises():
    with pytest.raises(AnalysisParamError):
        validate_constraint({"where": {"face": "top"}, "type": "encastre"})


def test_missing_where_raises():
    with pytest.raises(AnalysisParamError):
        validate_constraint({"name": "x", "type": "encastre"})


def test_unknown_type_raises():
    with pytest.raises(AnalysisParamError):
        validate_constraint({"name": "x", "where": {"face": "top"}, "type": "welded"})


def test_dof_out_of_range_raises():
    with pytest.raises(AnalysisParamError):
        validate_constraint({"name": "x", "where": {"face": "top"}, "dof": [0, 7]})
