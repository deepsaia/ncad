from ncad.spec.feature_id_validator import FeatureIdValidator


def _doc(features):
    return {"schema_version": 1, "units": "mm",
            "parts": {"p": {"profile": "solid", "features": features}}}


def test_no_duplicates_is_clean():
    doc = _doc([{"id": "sk", "op": "sketch"}, {"id": "pad", "op": "extrude"}])
    assert FeatureIdValidator().validate(doc) == []


def test_duplicate_id_reported_by_id():
    doc = _doc([{"id": "a", "op": "sketch"}, {"id": "a", "op": "extrude"}])
    issues = FeatureIdValidator().validate(doc)
    assert len(issues) == 1
    assert "a" in issues[0].message


def test_duplicates_are_scoped_per_part():
    doc = {"schema_version": 1, "units": "mm", "parts": {
        "p1": {"profile": "solid", "features": [{"id": "x", "op": "sketch"}]},
        "p2": {"profile": "solid", "features": [{"id": "x", "op": "sketch"}]},
    }}
    assert FeatureIdValidator().validate(doc) == []
