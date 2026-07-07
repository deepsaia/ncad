from ncad.ops.groove_op import GrooveOp
from tests.kernel.fake_kernel import FakeKernel


def test_groove_cuts_revolved_tool_from_target():
    k = FakeKernel()
    target = k.revolve(k.polygon_face([(0, 0), (20, 0), (20, 10), (0, 10)], "XY"),
                       (0, 0, 0), (0, 1, 0))
    tool_profile = k.polygon_face([(8, 4), (12, 4), (12, 6), (8, 6)], "XY")
    result = GrooveOp().build(
        None, {"id": "grv", "axis": "Y",
               "__refs__": {"target": target, "profile": tool_profile}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) < k.volume(target)


def test_groove_no_target_reports_issue():
    k = FakeKernel()
    profile = k.polygon_face([(8, 4), (12, 4), (12, 6), (8, 6)], "XY")
    result = GrooveOp().build(
        None, {"id": "grv", "axis": "Y", "__refs__": {"profile": profile}}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
