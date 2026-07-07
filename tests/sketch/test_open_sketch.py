from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _open_l_path():
    # two connected line entities forming an open L (no closing edge)
    return {
        "id": "path", "op": "sketch", "plane": "XZ", "open": True,
        "entities": [
            {"id": "p0", "type": "point", "at": [0.0, 0.0]},
            {"id": "p1", "type": "point", "at": [0.0, 20.0]},
            {"id": "p2", "type": "point", "at": [15.0, 20.0]},
            {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
            {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
        ],
        "constraints": [{"type": "fix", "of": "p0"}, {"type": "fix", "of": "p1"},
                        {"type": "fix", "of": "p2"}],
    }


def test_open_sketch_yields_a_wire_with_length():
    k = FakeKernel()
    result = SketchOp().build(None, _open_l_path(), {}, k)
    assert result.shape is not None
    # the open L is 20 + 15 = 35 long
    assert round(k.wire_length(result.shape), 6) == 35.0


def test_open_sketch_does_not_close_or_error_on_open_chain():
    k = FakeKernel()
    result = SketchOp().build(None, _open_l_path(), {}, k)
    assert [i for i in result.issues if i.level == "error"] == []


def test_closed_sketch_unchanged_still_builds_face():
    k = FakeKernel()
    params = {"id": "sk", "op": "sketch", "plane": "XY",
              "elements": [{"id": "r", "type": "rectangle", "w": 10.0, "h": 10.0}]}
    result = SketchOp().build(None, params, {}, k)
    assert result.shape is not None
    assert k.volume(k.extrude(result.shape, 1.0)) == 100.0
