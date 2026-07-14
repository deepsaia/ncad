"""Expand a component-pattern instance into N placed instances (bucket 5.7).

An assembly instance may carry a ``pattern`` (linear/circular/table, the 3.x pattern vocabulary):
one referenced part placed at each pattern location. ComponentPattern mints born-once ids
``<id>/<n>`` and composes each pattern transform with the base instance's placement into a
``{position, rotation}`` placement (the AssemblyPlacement convention). Pure math; reuses
ncad.ops.pattern_placements so the placement semantics match the feature-level pattern exactly.
"""

import math

from ncad.assembly.assembly_placement import AssemblyPlacement, _rot_axis
from ncad.ops.pattern_params import PatternParamError, pattern_kwargs
from ncad.ops.pattern_placements import PatternPlacements


class ComponentPatternError(Exception):
    """A component pattern spec is invalid (bad kind / placement)."""


class ComponentPattern:
    """Expands a ``pattern``-bearing instance into born-once ordinal instances."""

    def __init__(self) -> None:
        self._placement = AssemblyPlacement()

    def expand(self, instance: dict) -> list[dict]:
        """Return the expanded instances, or ``[instance]`` when there is no pattern."""
        spec = instance.get("pattern")
        if not spec:
            return [instance]
        try:
            kwargs = pattern_kwargs(spec)
        except PatternParamError as exc:
            raise ComponentPatternError(str(exc)) from exc
        base = self._placement.matrix(instance.get("placement"), 1.0)
        try:
            placements = PatternPlacements(kwargs, anchor=_translation(base)).specs()
        except ValueError as exc:
            raise ComponentPatternError(str(exc)) from exc
        out: list[dict] = []
        for ordinal, transform in enumerate(placements):
            matrix = _compose(base, transform)
            copy = {key: value for key, value in instance.items() if key != "pattern"}
            copy["id"] = f"{instance['id']}/{ordinal}"
            copy["placement"] = _matrix_to_placement(matrix)
            out.append(copy)
        return out


def _translation(matrix: list[list[float]]) -> tuple[float, float, float]:
    return (matrix[3][0], matrix[3][1], matrix[3][2])


def _compose(base: list[list[float]], transform: dict) -> list[list[float]]:
    """Apply a pattern transform spec (move/rotate) to a base row-major 4x4."""
    matrix = [row[:] for row in base]
    if "rotate" in transform:
        spec = transform["rotate"]
        rot = _rot_axis(spec["axis"], math.radians(float(spec["angle"])))
        matrix = _rotate_about(matrix, rot, spec["about"])
    if "move" in transform:
        move = transform["move"]
        matrix[3][0] += move[0]
        matrix[3][1] += move[1]
        matrix[3][2] += move[2]
    return matrix


def _rotate_about(matrix: list[list[float]], rot: list[list[float]],
                  about: tuple) -> list[list[float]]:
    """Rotate a row-major pose about the line through ``about`` (rotate basis + translation)."""
    basis = [[matrix[i][j] for j in range(3)] for i in range(3)]
    rotated_basis = [[sum(basis[i][k] * rot[k][j] for k in range(3)) for j in range(3)]
                     for i in range(3)]
    t = (matrix[3][0] - about[0], matrix[3][1] - about[1], matrix[3][2] - about[2])
    rt = tuple(sum(rot[j][i] * t[j] for j in range(3)) for i in range(3))
    out = [[rotated_basis[0][0], rotated_basis[0][1], rotated_basis[0][2], 0.0],
           [rotated_basis[1][0], rotated_basis[1][1], rotated_basis[1][2], 0.0],
           [rotated_basis[2][0], rotated_basis[2][1], rotated_basis[2][2], 0.0],
           [rt[0] + about[0], rt[1] + about[1], rt[2] + about[2], 1.0]]
    return out


def _matrix_to_placement(matrix: list[list[float]]) -> dict:
    """Row-major 4x4 -> {position, rotation:{axis, angle}} (axis-angle from the 3x3 basis)."""
    axis, angle = _axis_angle(matrix)
    return {"position": [matrix[3][0], matrix[3][1], matrix[3][2]],
            "rotation": {"axis": list(axis), "angle": angle}}


def _axis_angle(matrix: list[list[float]]) -> tuple[tuple[float, float, float], float]:
    """Axis-angle (axis unit vector, angle in degrees) from a row-major rotation 3x3."""
    trace = matrix[0][0] + matrix[1][1] + matrix[2][2]
    cos_angle = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    angle = math.degrees(math.acos(cos_angle))
    if angle < 1e-9:
        return ((0.0, 0.0, 1.0), 0.0)
    # Off-diagonal terms give the rotation axis (row-major: R[i][j] with translation last row).
    axis = (matrix[2][1] - matrix[1][2], matrix[0][2] - matrix[2][0], matrix[1][0] - matrix[0][1])
    norm = math.sqrt(sum(c * c for c in axis))
    if norm < 1e-9:
        return ((0.0, 0.0, 1.0), angle)
    return ((axis[0] / norm, axis[1] / norm, axis[2] / norm), angle)
