from ncad.assembly.solve_outcome import SolveOutcome


def test_solve_outcome_holds_fields() -> None:
    o = SolveOutcome(placements={"a": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]},
                     dof=2, status="under_constrained", failing_ids=[])
    assert o.dof == 2
    assert o.status == "under_constrained"
    assert o.placements["a"][3] == [0, 0, 0, 1]
    assert o.failing_ids == []
