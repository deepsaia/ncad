import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.trace_extractor import TraceExtractor

# A placement is a row-major world 4x4: rows 0..2 the rotation (unit-free), row 3 the translation
# in METRES. Identity rotation + a translation of (tx, ty, tz) metres:


def _placement(tx, ty, tz, rot=None):
    r = rot or [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    return [[r[0][0], r[0][1], r[0][2], 0.0],
            [r[1][0], r[1][1], r[1][2], 0.0],
            [r[2][0], r[2][1], r[2][2], 0.0],
            [tx, ty, tz, 1.0]]


def _frame(**placements):
    return {"placements": placements}


def test_trace_pure_translation_point_in_metres():
    # Plunger at local point (0, 67, 0) mm; frames translate it by 0 then +0.02 m (=20 mm) in y.
    # World point (metres) = point_mm * to_metres (0.001) . R(identity) + t_metres.
    # frame0: (0, 0.067, 0); frame1: (0, 0.067 + 0.02, 0) = (0, 0.087, 0).
    specs = [{"id": "crown", "instance": "plunger", "point": (0.0, 67.0, 0.0), "connector": None}]
    frames = [_frame(plunger=_placement(0.0, 0.0, 0.0)),
              _frame(plunger=_placement(0.0, 0.02, 0.0))]
    traces = TraceExtractor().extract(specs, frames, {}, to_metres=0.001)
    assert len(traces) == 1
    t = traces[0]
    assert t["id"] == "crown" and t["instance"] == "plunger"
    assert len(t["polyline"]) == 2
    assert t["polyline"][0] == [0.0, 0.067, 0.0]
    assert math.isclose(t["polyline"][1][1], 0.087, abs_tol=1e-9)


def test_trace_with_rotation():
    # A 90 deg rotation about Z (row-major: row i = image of basis e_i). local +X (1,0,0) mm -> +Y.
    # R rows: e_x->(0,1,0), e_y->(-1,0,0), e_z->(0,0,1). point (10,0,0) mm -> world (0, 0.010, 0) m.
    rot = [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    specs = [{"id": "tip", "instance": "arm", "point": (10.0, 0.0, 0.0), "connector": None}]
    frames = [_frame(arm=_placement(0.0, 0.0, 0.0, rot))]
    traces = TraceExtractor().extract(specs, frames, {}, to_metres=0.001)
    p = traces[0]["polyline"][0]
    assert math.isclose(p[0], 0.0, abs_tol=1e-9)
    assert math.isclose(p[1], 0.010, abs_tol=1e-9)
    assert math.isclose(p[2], 0.0, abs_tol=1e-9)


def test_trace_by_connector_uses_local_frame_origin():
    # A connector ref resolves to the connector's local origin (mm) from local_frames.
    frame_obj = ConnectorFrame.from_axis((20.0, 0.0, 0.0), (0.0, 0.0, 1.0), None, None)
    local_frames = {"flywheel": {"pin": frame_obj}}
    specs = [{"id": "pinPath", "instance": "flywheel", "point": None, "connector": "pin"}]
    frames = [_frame(flywheel=_placement(0.0, 0.0, 0.0))]
    traces = TraceExtractor().extract(specs, frames, local_frames, to_metres=0.001)
    assert traces[0]["polyline"][0] == [0.020, 0.0, 0.0]  # 20 mm -> 0.020 m


def test_trace_missing_instance_placement_skips_frame_gracefully():
    # An instance absent from a frame's placements: that trace vertex is omitted (not a crash).
    specs = [{"id": "x", "instance": "ghost", "point": (0.0, 0.0, 0.0), "connector": None}]
    frames = [_frame(other=_placement(0.0, 0.0, 0.0))]
    traces = TraceExtractor().extract(specs, frames, {}, to_metres=0.001)
    assert traces[0]["polyline"] == []
