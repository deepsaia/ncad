from ncad.ops.sketch_status import SketchStatus


def test_to_dict_round_trips_fields():
    s = SketchStatus(feature_id="sk", status="over", dof=0, failing_ids=["c3", "c7"])
    assert s.to_dict() == {
        "feature_id": "sk", "status": "over", "dof": 0, "failing_ids": ["c3", "c7"],
    }


def test_defaults_empty_failing_ids():
    s = SketchStatus(feature_id="sk", status="well", dof=0)
    assert s.failing_ids == []
    assert s.to_dict()["failing_ids"] == []
