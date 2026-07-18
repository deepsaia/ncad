import pytest

from ncad.assembly.motion_outputs_spec import MotionOutputsError, MotionOutputsSpec


def test_parse_trace_with_point():
    traces, measures = MotionOutputsSpec().parse(
        {"traces": [{"id": "crownPath", "instance": "plunger", "point": [0, 67, 0]}]})
    assert measures == []
    assert len(traces) == 1
    t = traces[0]
    assert t["id"] == "crownPath" and t["instance"] == "plunger"
    assert t["point"] == (0.0, 67.0, 0.0) and t["connector"] is None


def test_parse_trace_with_connector():
    traces, _ = MotionOutputsSpec().parse(
        {"traces": [{"id": "pinPath", "instance": "flywheel", "connector": "pin"}]})
    assert traces[0]["connector"] == "pin" and traces[0]["point"] is None


def test_parse_coordinate_measure():
    _, measures = MotionOutputsSpec().parse(
        {"measures": [{"id": "stroke", "kind": "coordinate", "instance": "plunger",
                       "point": [0, 67, 0], "axis": "y"}]})
    m = measures[0]
    assert m["id"] == "stroke" and m["kind"] == "coordinate" and m["axis"] == "y"
    assert m["a"]["instance"] == "plunger" and m["a"]["point"] == (0.0, 67.0, 0.0)


def test_parse_distance_measure():
    _, measures = MotionOutputsSpec().parse(
        {"measures": [{"id": "throw", "kind": "distance",
                       "a": {"instance": "flywheel", "connector": "pin"},
                       "b": {"instance": "block", "connector": "main"}}]})
    m = measures[0]
    assert m["kind"] == "distance"
    assert m["a"]["connector"] == "pin" and m["b"]["connector"] == "main"


def test_parse_angle_measure():
    _, measures = MotionOutputsSpec().parse(
        {"measures": [{"id": "rodAngle", "kind": "angle",
                       "vertex": {"instance": "rod", "point": [20, 0, 0]},
                       "a": {"instance": "rod", "point": [0, 67, 0]},
                       "b": {"instance": "block", "connector": "main"}}]})
    m = measures[0]
    assert m["kind"] == "angle" and m["vertex"]["point"] == (20.0, 0.0, 0.0)


def test_parse_swept_volume_measure():
    _, measures = MotionOutputsSpec().parse(
        {"measures": [{"id": "stroke", "kind": "coordinate", "instance": "p",
                       "point": [0, 0, 0], "axis": "y"},
                      {"id": "vol", "kind": "swept_volume", "of": "stroke", "bore_d": 28}]})
    vol = measures[1]
    assert vol["kind"] == "swept_volume" and vol["of"] == "stroke" and vol["bore_d"] == 28.0


def test_empty_outputs_ok():
    traces, measures = MotionOutputsSpec().parse({})
    assert traces == [] and measures == []


def test_duplicate_trace_id_raises():
    with pytest.raises(MotionOutputsError, match="duplicate"):
        MotionOutputsSpec().parse(
            {"traces": [{"id": "p", "instance": "a", "point": [0, 0, 0]},
                        {"id": "p", "instance": "b", "point": [1, 0, 0]}]})


def test_trace_needs_point_or_connector_raises():
    with pytest.raises(MotionOutputsError):
        MotionOutputsSpec().parse({"traces": [{"id": "p", "instance": "a"}]})


def test_unknown_measure_kind_raises():
    with pytest.raises(MotionOutputsError, match="kind"):
        MotionOutputsSpec().parse(
            {"measures": [{"id": "m", "kind": "torque", "instance": "a", "point": [0, 0, 0]}]})


def test_coordinate_bad_axis_raises():
    with pytest.raises(MotionOutputsError, match="axis"):
        MotionOutputsSpec().parse(
            {"measures": [{"id": "m", "kind": "coordinate", "instance": "a",
                           "point": [0, 0, 0], "axis": "w"}]})


def test_swept_volume_unknown_ref_raises():
    with pytest.raises(MotionOutputsError, match="of"):
        MotionOutputsSpec().parse(
            {"measures": [{"id": "vol", "kind": "swept_volume", "of": "nope", "bore_d": 10}]})


def test_swept_volume_of_non_coordinate_raises():
    with pytest.raises(MotionOutputsError, match="coordinate"):
        MotionOutputsSpec().parse(
            {"measures": [{"id": "d", "kind": "distance",
                           "a": {"instance": "a", "point": [0, 0, 0]},
                           "b": {"instance": "b", "point": [1, 0, 0]}},
                          {"id": "vol", "kind": "swept_volume", "of": "d", "bore_d": 10}]})
