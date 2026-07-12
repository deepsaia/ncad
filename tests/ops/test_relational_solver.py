import math

from ncad.ops.relational_solver import RelationalSolver


def test_parallel_already_parallel_is_identity() -> None:
    # Two +Z faces are already parallel: no transform needed.
    solver = RelationalSolver()
    result = solver.solve("parallel", ((0, 0, 1), (0, 0, 0)), ((0, 0, 1), (5, 5, 10)))
    assert result is None


def test_parallel_rotates_normal_onto_reference() -> None:
    solver = RelationalSolver()
    # moving +X face onto a reference +Z face: a 90-degree rotation.
    result = solver.solve("parallel", ((0, 0, 1), (0, 0, 0)), ((1, 0, 0), (0, 0, 0)))
    assert result is not None
    assert result["rotate"] is not None
    assert math.isclose(result["rotate"]["angle"], 90.0)
    assert result["move"] == (0.0, 0.0, 0.0)


def test_coplanar_adds_translation_along_reference_normal() -> None:
    solver = RelationalSolver()
    # Two +Z faces at different heights: parallel already, so only a translation closes the gap.
    result = solver.solve("coplanar", ((0, 0, 1), (0, 0, 0)), ((0, 0, 1), (0, 0, 10)))
    assert result is not None
    # Move down 10 along Z to land on the reference plane (z=0).
    assert math.isclose(result["move"][2], -10.0, abs_tol=1e-9)


def test_perpendicular_targets_ninety_degrees() -> None:
    solver = RelationalSolver()
    # Two parallel +Z faces: to make them perpendicular, rotate 90 degrees.
    result = solver.solve("perpendicular", ((0, 0, 1), (0, 0, 0)), ((0, 0, 1), (0, 0, 0)))
    assert result is not None and result["rotate"] is not None
    assert math.isclose(abs(result["rotate"]["angle"]), 90.0, abs_tol=1e-9)


def test_symmetric_reflects_across_reference_plane() -> None:
    solver = RelationalSolver()
    # Reference +Z face at z=0; moving +Z face at z=10 >> its mirror lands at z=-10.
    result = solver.solve("symmetric", ((0, 0, 1), (0, 0, 0)), ((0, 0, 1), (0, 0, 10)))
    assert result is not None
    assert math.isclose(result["move"][2], -20.0, abs_tol=1e-9)
