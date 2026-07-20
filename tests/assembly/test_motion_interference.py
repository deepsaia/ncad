from ncad.assembly.motion_interference import MotionInterference


class _FakeKernel:
    # place returns (shape_id, translation_x_mm); distance/common_volume from two such tuples.
    def place(self, shape, matrix):
        return (shape, matrix[3][0])          # translation already in mm after _to_mm

    def distance(self, a, b):
        return abs(a[1] - b[1]) - 10.0        # 10mm blocks: overlap when centres < 10 mm apart

    def common_volume(self, a, b):
        overlap = 10.0 - abs(a[1] - b[1])
        return max(0.0, overlap) * 100.0


def _frame(t, xa_m, xb_m):
    def mat(x):
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1], [x, 0.0, 0.0]]
    return {"t": t, "driver_value": t * 360.0,
            "placements": {"a": mat(xa_m), "b": mat(xb_m)}}


def test_interference_events_flag_overlapping_frames():
    frames = [
        _frame(0.0, 0.0, 0.100),     # 100 mm apart: clear
        _frame(0.5, 0.0, 0.005),     # 5 mm apart: overlap (< 10)
        _frame(1.0, 0.0, 0.100),     # clear again
    ]
    shapes = {"a": "SA", "b": "SB"}
    events = MotionInterference(_FakeKernel()).events(
        pairs=[("a", "b")], shapes_by_id=shapes, frames=frames, to_metres=1e-3)
    assert len(events) == 1
    assert events[0]["frame"] == 1 and events[0]["a"] == "a" and events[0]["b"] == "b"
    assert events[0]["volume"] > 0.0


def test_no_events_when_all_clear():
    frames = [_frame(0.0, 0.0, 0.100), _frame(1.0, 0.0, 0.200)]
    events = MotionInterference(_FakeKernel()).events(
        pairs=None, shapes_by_id={"a": "SA", "b": "SB"}, frames=frames, to_metres=1e-3)
    assert events == []


def test_events_respects_declared_pairs_subset():
    frames = [_frame(0.0, 0.0, 0.005)]     # a<>b overlap (5 mm)
    frames[0]["placements"]["c"] = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0.006, 0.0, 0.0]]
    shapes = {"a": "SA", "b": "SB", "c": "SC"}
    # only watch a<>c (6 mm apart -> overlap), NOT a<>b
    events = MotionInterference(_FakeKernel()).events(
        pairs=[("a", "c")], shapes_by_id=shapes, frames=frames, to_metres=1e-3)
    assert {(e["a"], e["b"]) for e in events} == {("a", "c")}
