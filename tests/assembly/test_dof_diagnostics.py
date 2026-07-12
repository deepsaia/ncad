from ncad.assembly.diagnostic_report import DiagnosticReport
from ncad.assembly.dof_diagnostics import PRIMITIVE_DOF, DofDiagnostics
from ncad.assembly.solve_outcome import SolveOutcome


def _outcome(dof=0, code=0, failing=None, redundant=None) -> SolveOutcome:
    return SolveOutcome(placements={}, dof=dof, status="", failing_ids=failing or [],
                        solve_code=code, redundant_ids=redundant or [])


_NET = {"bodies": 2, "grounded": 1, "removed": 6}


def test_well_constrained() -> None:
    r = DofDiagnostics().analyze(_outcome(dof=0, code=0), _NET)
    assert isinstance(r, DiagnosticReport)
    assert r.status == "well_constrained"
    assert r.under_constrained_hint is None


def test_under_constrained_sets_hint() -> None:
    r = DofDiagnostics().analyze(_outcome(dof=2, code=0), _NET)
    assert r.status == "under_constrained"
    assert r.under_constrained_hint == "assembly can still move; 2 free DoF"


def test_over_constrained_from_failing() -> None:
    r = DofDiagnostics().analyze(_outcome(dof=0, code=1, failing=["m2"]), _NET)
    assert r.status == "over_constrained"
    assert r.failing_ids == ["m2"]


def test_redundant_when_solver_reports_redundant() -> None:
    r = DofDiagnostics().analyze(_outcome(dof=0, code=5, redundant=["m3"]), _NET)
    assert r.status == "redundant"
    assert r.redundant_ids == ["m3"]


def test_redundant_headline_wins_over_free_dof() -> None:
    # Redundant AND under-constrained: redundant is the headline, dof carried in the explanation.
    r = DofDiagnostics().analyze(_outcome(dof=1, code=5, redundant=["m3"]), _NET)
    assert r.status == "redundant"
    assert "1 free DoF" in r.explanation


def test_explanation_string_exact() -> None:
    r = DofDiagnostics().analyze(_outcome(dof=2, code=0),
                                 {"bodies": 3, "grounded": 1, "removed": 10})
    expected = "3 bodies (18 DoF), 1 grounded (-6), mates removing 10 DoF >> 2 free DoF"
    assert r.explanation == expected


def test_primitive_dof_table_has_all_kinds() -> None:
    for kind in ("points_coincident", "axes_coincident", "point_in_plane", "point_plane_distance",
                 "points_distance", "parallel_dirs", "anti_parallel_dirs", "dirs_angle", "lock"):
        assert kind in PRIMITIVE_DOF


def test_deterministic() -> None:
    a = DofDiagnostics().analyze(_outcome(dof=0, code=5, redundant=["m3"]), _NET)
    b = DofDiagnostics().analyze(_outcome(dof=0, code=5, redundant=["m3"]), _NET)
    assert a.to_dict() == b.to_dict()
