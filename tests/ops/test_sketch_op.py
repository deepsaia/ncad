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


def test_project_and_offset_builds_a_face():
    kernel = FakeKernel()

    class _Passthrough(SketchSolver):
        def solve(self, entities, constraints, feature_id):
            positions = {e["id"]: tuple(e["at"]) for e in entities if e["type"] == "point"}
            return SolveResult(positions=positions, dof=0, status="well_constrained",
                               issues=[], radii={})

    # __refs__["project"] carries 2D descriptors (FakeKernel.project_edges is identity):
    # the projected square is construction (excluded from the wire); an inner real square
    # is what gets built.
    feature = {
        "id": "sk", "op": "sketch", "plane": "XY",
        "project": ["ignored-by-stub"],
        "__refs__": {"project": [
            {"kind": "line", "points": [(0.0, 0.0), (40.0, 0.0)]},
            {"kind": "line", "points": [(40.0, 0.0), (40.0, 40.0)]},
            {"kind": "line", "points": [(40.0, 40.0), (0.0, 40.0)]},
            {"kind": "line", "points": [(0.0, 40.0), (0.0, 0.0)]},
        ]},
        "entities": [
            {"id": "q0", "type": "point", "at": [5, 5]},
            {"id": "q1", "type": "point", "at": [35, 5]},
            {"id": "q2", "type": "point", "at": [35, 35]},
            {"id": "q3", "type": "point", "at": [5, 35]},
            {"id": "m0", "type": "line", "p1": "q0", "p2": "q1"},
            {"id": "m1", "type": "line", "p1": "q1", "p2": "q2"},
            {"id": "m2", "type": "line", "p1": "q2", "p2": "q3"},
            {"id": "m3", "type": "line", "p1": "q3", "p2": "q0"},
        ],
        "constraints": [],
    }
    result = SketchOp(_Passthrough()).build(None, feature, {}, kernel)
    assert result.shape is not None
    # inner 30x30 loop built; projected construction square excluded
    assert kernel.volume(kernel.extrude(result.shape, 1.0)) == 900.0


def test_transform_mirror_builds_face() -> None:
    kernel = FakeKernel()
    # a half-vee mirrored across the Y axis closes into a single loop and builds
    params = {
        "id": "sk", "op": "sketch", "plane": "XY",
        "entities": [
            {"id": "apex", "type": "point", "at": [0.0, 0.0]},
            {"id": "top", "type": "point", "at": [0.0, 10.0]},
            {"id": "right", "type": "point", "at": [5.0, 5.0]},
            {"id": "s0", "type": "line", "p1": "top", "p2": "right"},
            {"id": "s1", "type": "line", "p1": "right", "p2": "apex"},
        ],
        # apex + top weld onto the axis (pinned by the fixed mirror copies), so only the
        # free reflecting point `right` needs fixing; pinning apex/top too over-constrains.
        "constraints": [{"type": "fix", "of": "right"}],
        "transforms": [
            {"id": "m", "op": "mirror", "sources": ["s0", "s1"],
             "axis": {"p1": "apex", "p2": "top"}},
        ],
    }
    result = SketchOp().build(None, params, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors == [] and result.shape is not None


def test_transform_error_surfaces_as_issue() -> None:
    kernel = FakeKernel()
    params = {
        "id": "sk", "op": "sketch", "plane": "XY",
        "entities": [{"id": "p0", "type": "point", "at": [0.0, 0.0]}],
        "constraints": [],
        "transforms": [{"op": "warp", "sources": ["p0"]}],
    }
    result = SketchOp().build(None, params, {}, kernel)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_modify_trim_then_build() -> None:
    kernel = FakeKernel()
    # a square with an overshooting top edge, trimmed back to close the loop, builds.
    params = {
        "id": "sk", "op": "sketch", "plane": "XY",
        "entities": [
            {"id": "p0", "type": "point", "at": [0.0, 0.0]},
            {"id": "p1", "type": "point", "at": [10.0, 0.0]},
            {"id": "p2", "type": "point", "at": [10.0, 10.0]},
            {"id": "tl", "type": "point", "at": [0.0, 10.0]},
            {"id": "tr", "type": "point", "at": [20.0, 10.0]},
            {"id": "bot", "type": "line", "p1": "p0", "p2": "p1"},
            {"id": "right", "type": "line", "p1": "p1", "p2": "p2"},
            {"id": "top", "type": "line", "p1": "tl", "p2": "tr"},
            {"id": "left", "type": "line", "p1": "tl", "p2": "p0"},
        ],
        # the trimmed `top` is fixed and pins its endpoints tl + p2, so only the other
        # corners (p0, p1) need an explicit fix; pinning tl/p2 too would over-constrain.
        "constraints": [
            {"type": "fix", "of": "p0"}, {"type": "fix", "of": "p1"},
        ],
        "modify": [
            {"id": "cut", "op": "trim", "of": "top", "at": "right", "keep": "tl"},
        ],
    }
    result = SketchOp().build(None, params, {}, kernel)
    errors = [i for i in result.issues if i.level == "error"]
    assert errors == [] and result.shape is not None


def test_modify_error_surfaces_as_issue() -> None:
    kernel = FakeKernel()
    params = {
        "id": "sk", "op": "sketch", "plane": "XY",
        "entities": [
            {"id": "a0", "type": "point", "at": [0.0, 0.0]},
            {"id": "a1", "type": "point", "at": [10.0, 0.0]},
            {"id": "b0", "type": "point", "at": [0.0, 3.0]},
            {"id": "b1", "type": "point", "at": [10.0, 3.0]},
            {"id": "la", "type": "line", "p1": "a0", "p2": "a1"},
            {"id": "lb", "type": "line", "p1": "b0", "p2": "b1"},
        ],
        "constraints": [],
        "modify": [{"id": "t", "op": "trim", "of": "la", "at": "lb", "keep": "a0"}],
    }
    result = SketchOp().build(None, params, {}, kernel)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
