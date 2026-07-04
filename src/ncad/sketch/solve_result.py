"""The result of solving a sketch's entities + constraints (design section 5).

Carries the solved 2D point positions plus the solve status (well / under / over
constrained / inconsistent), the remaining degrees of freedom, and any id-tagged
issues (an inconsistent solve reports errors; an under-constrained solve reports a
warning). Returned by every SketchSolver so the SketchOp is solver-agnostic.
"""

from dataclasses import dataclass

from ncad.ops.build_issue import BuildIssue


@dataclass(frozen=True)
class SolveResult:
    """Solved positions and status for a sketch."""

    positions: dict[str, tuple[float, float]]
    dof: int
    status: str
    issues: list[BuildIssue]
