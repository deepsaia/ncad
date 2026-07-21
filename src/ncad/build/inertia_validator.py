"""Validate that a body's mass-moment-of-inertia tensor is physically realizable.

ncad computes inertia from real B-rep mass properties (MassCalculator over the kernel), so this is a
self-check on that computed tensor, not a substitute for it: a tensor that fails these is a symptom
of a bad density, a degenerate solid, or a units error. The checks are the standard necessary
conditions for a rigid-body inertia tensor about its centroid:

- mass > 0 (a massless-but-present body is a material/density error);
- the diagonal moments are strictly positive;
- the triangle inequalities hold: each principal/diagonal moment <= the sum of the other two
  (Ixx <= Iyy + Izz, and permutations) - a necessary condition for a real mass distribution;
- the tensor is positive-semidefinite (all leading principal minors >= 0 and det >= 0) - the full
  matrix condition, which also catches bad off-diagonal (product-of-inertia) terms.

Returns coded Diagnostics (``invalid_inertia``, warning severity - it never blocks a build; a
physically-odd tensor is worth surfacing, not fatal). Pure math over the tensor dict; one class.
"""

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic

# Tolerance for the "strictly positive" / inequality tests: treat magnitudes below this (relative to
# the tensor scale) as zero so float noise on a valid tensor does not trip a warning.
_TOL = 1e-9


class InertiaValidator:
    """Flags a per-body inertia tensor that is not a physically realizable rigid-body tensor."""

    def check(self, part_name: str, body_id: str, mass: float | None,
              inertia: dict | None) -> list[Diagnostic]:
        """Return inertia Diagnostics for one body (empty when the tensor is plausible or absent).

        ``inertia`` is the MassCalculator shape ``{"matrix": 3x3, "principal": [..]}``; None (no
        material/density) skips the check - absence is not an error here.
        """
        if inertia is None:
            return []
        matrix = _as_3x3(inertia.get("matrix"))
        if matrix is None:
            return [self._diag(part_name, body_id, "inertia tensor is not a 3x3 matrix")]
        problems: list[str] = []
        if mass is not None and mass <= _TOL:
            problems.append(f"mass {mass!r} is not positive")
        scale = max((abs(matrix[i][i]) for i in range(3)), default=0.0)
        tol = _TOL * max(scale, 1.0)
        diag = [matrix[i][i] for i in range(3)]
        if any(d <= tol for d in diag):
            problems.append(f"diagonal moments {diag} are not all positive")
        elif not _triangle_ok(diag, tol):
            problems.append(f"diagonal moments {diag} violate the triangle inequality")
        if not _psd(matrix, tol):
            problems.append("tensor is not positive-semidefinite")
        return [self._diag(part_name, body_id, "; ".join(problems))] if problems else []

    def _diag(self, part_name: str, body_id: str, detail: str) -> Diagnostic:
        return Diagnostic(
            severity="warning", code=codes.INVALID_INERTIA,
            location=f"parts.{part_name}.bodies.{body_id}",
            message=f"body {body_id!r} has a non-physical inertia tensor: {detail}",
            hint="check the material density and that the body is a valid closed solid",
            stage="build")


def _as_3x3(matrix: object) -> list[list[float]] | None:
    """The matrix as a 3x3 float grid if it is one, else None (so the caller narrows the type)."""
    if (isinstance(matrix, list) and len(matrix) == 3
            and all(isinstance(row, list) and len(row) == 3 for row in matrix)):
        return [[float(c) for c in row] for row in matrix]
    return None


def _triangle_ok(diag: list[float], tol: float) -> bool:
    """Each diagonal moment must not exceed the sum of the other two (within tolerance)."""
    a, b, c = diag
    return a <= b + c + tol and b <= a + c + tol and c <= a + b + tol


def _psd(m: list[list[float]], tol: float) -> bool:
    """Positive-semidefinite test for a symmetric 3x3 via leading principal minors + determinant."""
    m11 = m[0][0]
    m2 = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
           - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
           + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    return m11 >= -tol and m2 >= -tol and det >= -tol
