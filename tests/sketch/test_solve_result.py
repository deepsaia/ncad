from ncad.ops.build_issue import BuildIssue
from ncad.sketch.solve_result import SolveResult


def test_solve_result_fields():
    r = SolveResult(positions={"p0": (0.0, 0.0)}, dof=0, status="well_constrained",
                    issues=[])
    assert r.positions["p0"] == (0.0, 0.0)
    assert r.dof == 0 and r.status == "well_constrained" and r.issues == []


def test_solve_result_carries_issues():
    issue = BuildIssue(node_id="sk", message="bad", level="error")
    r = SolveResult(positions={}, dof=3, status="inconsistent", issues=[issue])
    assert r.issues[0].node_id == "sk"


def test_solve_result_radii_defaults_empty():
    r = SolveResult(positions={}, dof=0, status="well_constrained", issues=[])
    assert r.radii == {}


def test_solve_result_carries_radii():
    r = SolveResult(positions={}, dof=0, status="well_constrained", issues=[],
                    radii={"c0": 8.0})
    assert r.radii["c0"] == 8.0


def test_solve_result_measurements_defaults_empty():
    r = SolveResult(positions={}, dof=0, status="well_constrained", issues=[])
    assert r.measurements == {}


def test_solve_result_carries_measurements():
    r = SolveResult(positions={}, dof=0, status="well_constrained", issues=[],
                    measurements={"m1": 27.3})
    assert r.measurements["m1"] == 27.3
