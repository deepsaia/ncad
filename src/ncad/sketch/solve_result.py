"""The result of solving a sketch's entities + constraints.

Carries the solved 2D point positions plus the solve status (well / under / over
constrained / inconsistent), the remaining degrees of freedom, and any id-tagged
issues (an inconsistent solve reports errors; an under-constrained solve reports a
warning). Returned by every SketchSolver so the SketchOp is solver-agnostic.
"""

from dataclasses import dataclass, field

from ncad.ops.build_issue import BuildIssue


@dataclass(frozen=True)
class SolveResult:
    """Solved positions and status for a sketch.

    :ivar radii: Solved radius per circle/arc entity id (empty for line-only sketches).
    :ivar measurements: Measured value per driven (reference) dimension id (empty when
        the sketch has no driven dimensions).
    :ivar failing_ids: Ids of the authored constraints the solver reported as failing
        (empty unless over-constrained/inconsistent); in declaration order.
    """

    positions: dict[str, tuple[float, float]]
    dof: int
    status: str
    issues: list[BuildIssue]
    radii: dict[str, float] = field(default_factory=dict)
    measurements: dict[str, float] = field(default_factory=dict)
    failing_ids: list[str] = field(default_factory=list)
