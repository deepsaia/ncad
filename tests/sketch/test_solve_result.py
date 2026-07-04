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
