"""Interpret an assembly solve into a legible, id-attributed DiagnosticReport (bucket 5.3).

Pure interpretation over the raw solver signals (no py-slvs, no kernel): the four-state status
(well/under/over/redundant), a plain-language DoF explanation built from cheap counts, and the
failing/redundant id split. The 3D analogue of the sketch-status legibility layer (bucket 1.5): a
"better than a bare solver" DoF-diagnostics layer over py-slvs. Home for a future nested-sparsity
pebble-game screen.
"""

import logging

from ncad.assembly.diagnostic_report import DiagnosticReport
from ncad.assembly.solve_outcome import SolveOutcome

logger = logging.getLogger(__name__)

# DoF removed by each normal-form primitive (used only for the NOMINAL explanation count; the
# solver's actual dof is authoritative). Matches the kinds MateLowering emits.
PRIMITIVE_DOF = {
    "points_coincident": 3, "axes_coincident": 4, "point_in_plane": 1,
    "point_plane_distance": 1, "points_distance": 1, "parallel_dirs": 2,
    "anti_parallel_dirs": 2, "dirs_angle": 1, "lock": 6,
    # Joint primitives (bucket 5.4a): secondary_parallel blocks spin (2, like parallel_dirs);
    # point_on_line pins a point to a line (2 translational DoF removed).
    "secondary_parallel": 2, "point_on_line": 2,
}

_GENUINE_FAILURE_CODES = frozenset({1, 2, 3})


class DofDiagnostics:
    """Interprets a SolveOutcome + a network summary into a DiagnosticReport."""

    def analyze(self, outcome: SolveOutcome, network: dict) -> DiagnosticReport:
        """Return the four-state diagnostic report for a solved assembly."""
        status = self._status(outcome)
        explanation = self._explain(network, outcome.dof)
        hint = (f"assembly can still move; {outcome.dof} free DoF"
                if outcome.dof > 0 else None)
        return DiagnosticReport(status=status, dof=outcome.dof, explanation=explanation,
                                failing_ids=list(outcome.failing_ids),
                                redundant_ids=list(outcome.redundant_ids),
                                under_constrained_hint=hint)

    def _status(self, outcome: SolveOutcome) -> str:
        """Four-state precedence: genuine conflict, then redundancy, then free DoF, then rigid."""
        if outcome.failing_ids or outcome.solve_code in _GENUINE_FAILURE_CODES:
            return "over_constrained"
        if outcome.redundant_ids:
            return "redundant"
        if outcome.dof > 0:
            return "under_constrained"
        return "well_constrained"

    def _explain(self, network: dict, dof: int) -> str:
        """Plain-language DoF accounting from cheap counts; the solver's dof is authoritative."""
        bodies = int(network.get("bodies", 0))
        grounded = int(network.get("grounded", 0))
        removed = int(network.get("removed", 0))
        base = (f"{bodies} bodies ({6 * bodies} DoF), {grounded} grounded (-{6 * grounded}), "
                f"mates removing {removed} DoF >> {dof} free DoF")
        couplings = int(network.get("couplings", 0))
        if couplings > 0:
            # Report, don't count: couplings enforce nothing in 5.4b (Phase 6 does), so the dof
            # number stays truthful to what is enforced; we only surface the declared intent.
            plural = "s" if couplings != 1 else ""
            base += f"; + {couplings} declared coupling{plural} (enforced in motion)"
        return base
