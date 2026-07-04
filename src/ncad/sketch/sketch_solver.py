"""Abstract geometric-constraint solver seam (design sections 5, 16).

The sketch layer talks only to this interface, so the solver is swappable (py-slvs /
SolveSpace today, planegcs later) without touching the schema or the sketch op. The
solver works purely in 2D sketch coordinates; the op places the solved wire on the
feature's plane.
"""

from abc import ABC, abstractmethod

from ncad.sketch.solve_result import SolveResult


class SketchSolver(ABC):
    """Solves a sketch's 2D entities + constraints to positions."""

    @abstractmethod
    def solve(self, entities: list[dict], constraints: list[dict],
              feature_id: str) -> SolveResult:
        """Solve ``entities`` under ``constraints``; ``feature_id`` tags any issues."""
