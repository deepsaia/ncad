import pytest

from ncad.fea.analysis_params import AnalysisParamError, validate_constraint, validate_load


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


def test_force_needs_vector():
    load = validate_load({"name": "pull", "where": {"face": "top"}, "type": "force",
                          "vector": [0, -500, 0]})
    assert load["type"] == "force" and load["vector"] == [0.0, -500.0, 0.0]


def test_pressure_needs_magnitude():
    load = validate_load({"name": "tip", "where": {"face": "top"}, "type": "pressure",
                          "magnitude": 2.5e5})
    assert load["magnitude"] == 2.5e5


def test_gravity_takes_no_where_and_needs_direction():
    load = validate_load({"name": "wt", "type": "gravity", "g": 9.81,
                          "direction": [0, 0, -1]})
    assert load["g"] == 9.81 and load["direction"] == [0.0, 0.0, -1.0]
    assert "where" not in load or load["where"] is None


def test_film_needs_sink_and_coefficient():
    load = validate_load({"name": "conv", "where": {"face": "all"}, "type": "film",
                          "sink": 20, "coefficient": 15})
    assert load["sink"] == 20.0 and load["coefficient"] == 15.0


def test_temperature_load_needs_value():
    load = validate_load({"name": "hot", "where": {"face": "bottom"}, "type": "temperature",
                          "value": 80})
    assert load["value"] == 80.0


def test_force_without_vector_raises():
    with pytest.raises(AnalysisParamError):
        validate_load({"name": "x", "where": {"face": "top"}, "type": "force"})


def test_pressure_without_where_raises():
    with pytest.raises(AnalysisParamError):
        validate_load({"name": "x", "type": "pressure", "magnitude": 1.0})


def test_unknown_load_type_raises():
    with pytest.raises(AnalysisParamError):
        validate_load({"name": "x", "where": {"face": "top"}, "type": "torque"})
