"""Solve a driven mechanism over time: re-run the static MateSolver at each driver value.

Kinematic motion (design section 8): the joint graph defines DoF, a driver sweeps one, and each step
re-solves the position network with that step's DRIVER PIN injected. Each step seeds from the prior
step's solved placements (continuity, so the solver tracks one branch instead of jumping). A step
that fails to converge carries the prior good placements + its own status, so the trajectory is
partial rather than aborting. Force dynamics is Phase 14; this is positions only.
"""

import logging

from ncad.assembly.mate_solver import MateSolver
from ncad.assembly.solve_outcome import SolveOutcome

logger = logging.getLogger(__name__)


class MotionSolver:
    """Re-solves the position network at each driver value, returning a trajectory."""

    def __init__(self) -> None:
        self._solver = MateSolver()

    def solve(self, bodies: dict, primitives: list[dict], ground_ids: set, seeds: dict,
              driver_prims_per_value: list[list[dict]]) -> list[SolveOutcome]:
        """One SolveOutcome per driver value; each step seeds from the prior step's placements."""
        outcomes: list[SolveOutcome] = []
        current_seed = dict(seeds)
        last_good = dict(seeds)
        for step_prims in driver_prims_per_value:
            try:
                outcome = self._solver.solve(
                    bodies, [*primitives, *step_prims], ground_ids, current_seed)
            except (ValueError, KeyError) as exc:
                logger.warning("motion step failed: %s", exc)
                outcomes.append(SolveOutcome(placements=dict(last_good), dof=0,
                                             status="failed", solve_code=-1))
                continue
            outcomes.append(outcome)
            if outcome.status != "over_constrained":
                current_seed = dict(outcome.placements)
                last_good = dict(outcome.placements)
        return outcomes
