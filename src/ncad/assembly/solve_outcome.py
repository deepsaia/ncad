"""The typed result of an assembly constraint solve.

Small value object returned by MateSolver: the solved per-instance placement matrices (mm,
row-major, same convention as AssemblyPlacement), the free-DoF count, an over/under/solved status,
and the ids of any failing (over-constrained) mates. Rich diagnostics (rank interpretation,
redundancy root-causing) are bucket 5.3; this carries only what py-slvs reports directly.
"""

from dataclasses import dataclass, field


@dataclass
class SolveOutcome:
    """Solved placements + minimal constraint status from a MateSolver run."""

    placements: dict[str, list[list[float]]]
    dof: int
    status: str
    failing_ids: list[str] = field(default_factory=list)
    # Raw signals for the 5.3 diagnostics layer: the py-slvs solve code and the redundant-but-
    # consistent constraint ids (code 5). DofDiagnostics interprets these; the solver stays numeric.
    solve_code: int = 0
    redundant_ids: list[str] = field(default_factory=list)
