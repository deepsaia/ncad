import pytest

from ncad.sketch.sketch_solver import SketchSolver


def test_sketch_solver_is_abstract():
    with pytest.raises(TypeError):
        SketchSolver()


def test_subclass_must_implement_solve():
    from ncad.sketch.solve_result import SolveResult

    class Stub(SketchSolver):
        def solve(self, entities, constraints, feature_id):
            return SolveResult(positions={}, dof=0, status="well_constrained", issues=[])

    assert Stub().solve([], [], "sk").status == "well_constrained"
