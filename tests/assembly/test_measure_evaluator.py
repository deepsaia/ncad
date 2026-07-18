import math

from ncad.assembly.measure_evaluator import MeasureEvaluator


def _placement(tx_m, ty_m, tz_m):
    # Identity rotation, translation in METRES (rows 0..2 rotation, row 3 translation).
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
            [tx_m, ty_m, tz_m, 1.0]]


def _frame(**placements):
    return {"placements": placements}


def _pt(instance, x, y, z):
    return {"instance": instance, "point": (x, y, z), "connector": None}


def test_coordinate_measure_series_in_mm():
    # Plunger crown local (0,67,0) mm; frames add +0 then +0.02 m to y. World-y mm: 67, 87.
    specs = [{"id": "stroke", "kind": "coordinate", "axis": "y",
              "a": _pt("plunger", 0.0, 67.0, 0.0)}]
    frames = [_frame(plunger=_placement(0.0, 0.0, 0.0)),
              _frame(plunger=_placement(0.0, 0.02, 0.0))]
    out = MeasureEvaluator().evaluate(specs, frames, {}, to_metres=0.001)
    m = out[0]
    assert m["id"] == "stroke" and m["kind"] == "coordinate" and m["unit"] == "mm"
    assert math.isclose(m["series"][0], 67.0, abs_tol=1e-9)
    assert math.isclose(m["series"][1], 87.0, abs_tol=1e-9)
    assert math.isclose(m["min"], 67.0, abs_tol=1e-9) and math.isclose(m["max"], 87.0, abs_tol=1e-9)


def test_distance_measure_in_mm():
    # a at (0,0,0), b at (30,0,0) mm, both on instances at origin -> distance 30 mm, constant.
    specs = [{"id": "throw", "kind": "distance",
              "a": _pt("crank", 0.0, 0.0, 0.0), "b": _pt("crank", 30.0, 0.0, 0.0)}]
    frames = [_frame(crank=_placement(0.0, 0.0, 0.0))]
    out = MeasureEvaluator().evaluate(specs, frames, {}, to_metres=0.001)
    m = out[0]
    assert m["unit"] == "mm" and math.isclose(m["series"][0], 30.0, abs_tol=1e-9)


def test_angle_measure_in_degrees():
    # vertex at origin, a along +X, b along +Y -> 90 degrees.
    specs = [{"id": "ang", "kind": "angle",
              "vertex": _pt("p", 0.0, 0.0, 0.0),
              "a": _pt("p", 10.0, 0.0, 0.0), "b": _pt("p", 0.0, 10.0, 0.0)}]
    frames = [_frame(p=_placement(0.0, 0.0, 0.0))]
    out = MeasureEvaluator().evaluate(specs, frames, {}, to_metres=0.001)
    assert out[0]["unit"] == "deg" and math.isclose(out[0]["series"][0], 90.0, abs_tol=1e-6)


def test_swept_volume_in_ml():
    # stroke goes 67..87 mm (travel 20 mm); bore_d 28 mm -> pi/4 * 28^2 * 20 mm^3 / 1000 = mL.
    specs = [{"id": "stroke", "kind": "coordinate", "axis": "y", "a": _pt("pl", 0.0, 67.0, 0.0)},
             {"id": "vol", "kind": "swept_volume", "of": "stroke", "bore_d": 28.0}]
    frames = [_frame(pl=_placement(0.0, 0.0, 0.0)), _frame(pl=_placement(0.0, 0.02, 0.0))]
    out = MeasureEvaluator().evaluate(specs, frames, {}, to_metres=0.001)
    vol = next(m for m in out if m["id"] == "vol")
    expected_ml = math.pi / 4.0 * 28.0 ** 2 * 20.0 / 1000.0
    assert vol["kind"] == "swept_volume" and vol["unit"] == "mL" and vol["of"] == "stroke"
    assert math.isclose(vol["value"], expected_ml, rel_tol=1e-9)
    # swept-so-far series: |value_i - min| * area / 1000; frame0 at min -> 0, frame1 full.
    assert math.isclose(vol["series"][0], 0.0, abs_tol=1e-9)
    assert math.isclose(vol["series"][1], expected_ml, rel_tol=1e-9)


def test_series_length_matches_frames():
    specs = [{"id": "s", "kind": "coordinate", "axis": "x", "a": _pt("p", 1.0, 0.0, 0.0)}]
    frames = [_frame(p=_placement(0.0, 0.0, 0.0)) for _ in range(5)]
    out = MeasureEvaluator().evaluate(specs, frames, {}, to_metres=0.001)
    assert len(out[0]["series"]) == 5
