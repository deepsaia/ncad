import pytest

from ncad.ops.build_issue import BuildIssue
from ncad.ops.sketch_op import SketchOp
from ncad.sketch.sketch_solver import SketchSolver
from ncad.sketch.solve_result import SolveResult
from tests.kernel.fake_kernel import FakeKernel


def _rect_feature() -> dict:
    return {
        "id": "sk",
        "op": "sketch",
        "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
    }


def test_sketch_builds_a_face_with_expected_area() -> None:
    kernel = FakeKernel()

    result = SketchOp().build(None, _rect_feature(), {}, kernel)

    assert result.issues == []
    # A rectangle face extruded by 1 gives volume == area.
    solid = kernel.extrude(result.shape, 1.0)
    assert kernel.volume(solid) == 80.0 * 60.0


def test_sketch_with_unknown_element_reports_issue_by_id() -> None:
    kernel = FakeKernel()
    feature = _rect_feature()
    feature["elements"][0]["type"] = "trapezoid"

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "sk"


def test_sketch_circle_area() -> None:
    import math

    kernel = FakeKernel()
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "elements": [{"id": "c", "type": "circle", "d": 20.0}]}

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.issues == []
    area = kernel.volume(kernel.extrude(result.shape, 1.0))
    assert area == pytest.approx(math.pi * 100.0, rel=0.02)


def test_sketch_polygon_from_points() -> None:
    kernel = FakeKernel()
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "elements": [{"id": "p", "type": "polygon",
                             "points": [[0, 0], [40, 0], [40, 30], [0, 30]]}]}

    result = SketchOp().build(None, feature, {}, kernel)

    assert result.issues == []
    assert kernel.volume(kernel.extrude(result.shape, 1.0)) == pytest.approx(1200.0)


class _StubSolver(SketchSolver):
    def __init__(self, result):
        self._result = result

    def solve(self, entities, constraints, feature_id):
        return self._result


def _square_feature():
    return {"id": "sk", "op": "sketch", "plane": "XY",
            "entities": [
                {"id": "p0", "type": "point", "at": [0, 0]},
                {"id": "p1", "type": "point", "at": [40, 0]},
                {"id": "p2", "type": "point", "at": [40, 40]},
                {"id": "p3", "type": "point", "at": [0, 40]},
                {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
                {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
                {"id": "l2", "type": "line", "p1": "p2", "p2": "p3"},
                {"id": "l3", "type": "line", "p1": "p3", "p2": "p0"}],
            "constraints": []}


def test_entities_path_builds_a_face():
    kernel = FakeKernel()
    solved = SolveResult(
        positions={"p0": (0.0, 0.0), "p1": (40.0, 0.0), "p2": (40.0, 40.0),
                   "p3": (0.0, 40.0)},
        dof=0, status="well_constrained", issues=[])
    result = SketchOp(_StubSolver(solved)).build(None, _square_feature(), {}, kernel)

    assert result.issues == [] and result.shape is not None
    assert kernel.volume(kernel.extrude(result.shape, 1.0)) == 1600.0


def test_entities_path_under_constrained_still_builds_with_warning():
    kernel = FakeKernel()
    solved = SolveResult(
        positions={"p0": (0.0, 0.0), "p1": (40.0, 0.0), "p2": (40.0, 40.0),
                   "p3": (0.0, 40.0)},
        dof=2, status="under_constrained",
        issues=[BuildIssue(node_id="sk", message="2 free DoF", level="warning")])
    result = SketchOp(_StubSolver(solved)).build(None, _square_feature(), {}, kernel)

    assert result.shape is not None
    assert result.issues and result.issues[0].level == "warning"


def test_entities_path_inconsistent_yields_no_shape():
    kernel = FakeKernel()
    solved = SolveResult(positions={}, dof=0, status="inconsistent",
                         issues=[BuildIssue(node_id="sk", message="conflict")])
    result = SketchOp(_StubSolver(solved)).build(None, _square_feature(), {}, kernel)

    assert result.shape is None and result.issues[0].node_id == "sk"


def test_primitive_elements_path_still_works():
    kernel = FakeKernel()
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 20}]}
    result = SketchOp().build(None, feature, {}, kernel)
    assert result.shape is not None and result.issues == []


def test_entities_path_builds_a_circle():
    kernel = FakeKernel()
    solved = SolveResult(
        positions={"cp": (0.0, 0.0)}, dof=0, status="well_constrained", issues=[],
        radii={"c0": 5.0})
    feature = {"id": "sk", "op": "sketch", "plane": "XY",
               "entities": [{"id": "cp", "type": "point", "at": [0, 0]},
                            {"id": "c0", "type": "circle", "center": "cp", "radius": 5}],
               "constraints": []}
    result = SketchOp(_StubSolver(solved)).build(None, feature, {}, kernel)
    import math
    assert result.shape is not None
    assert kernel.volume(kernel.extrude(result.shape, 1.0)) == pytest.approx(math.pi * 25.0)
