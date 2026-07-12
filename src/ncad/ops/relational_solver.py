"""Compute the one-shot rigid transform that satisfies a planar relation (design section 3).

A relation aligns a moving planar face's frame to a reference planar face's frame ONCE (no
maintenance, no solver, no DoF; that is Phase 5). Each relation reduces to a rotation of the
moving normal plus, for coplanar/symmetric, a translation along the reference normal. Pure
vector math over 3-tuples; deterministic.
"""

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

_EPS = 1e-9

Vec = tuple[float, float, float]
Frame = tuple[Vec, Vec]


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a: Vec) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec) -> Vec:
    n = _norm(a)
    if n < _EPS:
        return a
    return (a[0] / n, a[1] / n, a[2] / n)


def _scale(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


class RelationalSolver:
    """Computes the rigid transform for a one-shot planar relation."""

    def solve(self, relation: str, ref: Frame, moving: Frame) -> dict[str, Any] | None:
        """Return the transform for ``relation``, or None when already satisfied / degenerate."""
        if relation == "parallel":
            return self._align(ref, moving, target_dot=1.0, translate=False)
        if relation == "coplanar":
            return self._align(ref, moving, target_dot=1.0, translate=True)
        if relation == "perpendicular":
            return self._align(ref, moving, target_dot=0.0, translate=False)
        if relation == "symmetric":
            return self._symmetric(ref, moving)
        logger.warning("unknown relation %r", relation)
        return None

    def _align(self, ref: Frame, moving: Frame, target_dot: float,
               translate: bool) -> dict[str, Any] | None:
        n_ref, p_ref = _unit(ref[0]), ref[1]
        n_m, p_m = _unit(moving[0]), moving[1]
        rotate = self._rotation_to(n_m, p_m, n_ref, target_dot)
        move: Vec = (0.0, 0.0, 0.0)
        if translate:
            # After the (parallel) rotation about p_m, p_m is fixed, so close the gap along n_ref
            # so p_m lands on the reference plane.
            gap = _dot(_sub(p_ref, p_m), n_ref)
            move = _scale(n_ref, gap)
        if rotate is None and move == (0.0, 0.0, 0.0):
            return None
        return {"rotate": rotate, "move": move}

    def _rotation_to(self, n_m: Vec, p_m: Vec, n_ref: Vec,
                     target_dot: float) -> dict[str, Any] | None:
        current = max(-1.0, min(1.0, _dot(n_m, n_ref)))
        target_angle = math.degrees(math.acos(max(-1.0, min(1.0, target_dot))))
        current_angle = math.degrees(math.acos(current))
        delta = current_angle - target_angle
        if abs(delta) < _EPS:
            return None
        axis = _cross(n_m, n_ref)
        if _norm(axis) < _EPS:
            # Parallel or anti-parallel normals: pick any axis perpendicular to n_m.
            axis = _cross(n_m, (1.0, 0.0, 0.0))
            if _norm(axis) < _EPS:
                axis = _cross(n_m, (0.0, 1.0, 0.0))
        return {"axis": _unit(axis), "angle": delta, "about": p_m}

    def _symmetric(self, ref: Frame, moving: Frame) -> dict[str, Any] | None:
        # Reflect p_m across the reference plane (point p_ref, normal n_ref): the moving body
        # translates by -2 * (signed distance) along n_ref. Orientation is left to the translation
        # for a planar face (a full mirror is the mirror op; this is symmetric POSITION).
        n_ref = _unit(ref[0])
        p_ref, p_m = ref[1], moving[1]
        signed = _dot(_sub(p_m, p_ref), n_ref)
        if abs(signed) < _EPS:
            return None
        return {"rotate": None, "move": _scale(n_ref, -2.0 * signed)}
