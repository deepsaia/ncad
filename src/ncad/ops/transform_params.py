"""Parse and validate a transform feature's vocabulary into a transform description.

A transform names at least one of ``move`` ([dx,dy,dz]), ``rotate`` ({axis, angle, about}),
or ``scale`` (a uniform factor or [sx,sy,sz]), applied in the order scale >> rotate >> move.
``copy`` (default false) transforms in place; true adds a new body. A contract violation
raises TransformParamError (the op wraps it into a BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)

_AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


class TransformParamError(Exception):
    """A transform's move/rotate/scale vocabulary is missing or invalid."""


def transform_kwargs(params: dict) -> dict:
    """Return the validated transform description for a transform feature."""
    move = _vec3(params["move"], "move") if "move" in params else None
    rotate = _rotate(params["rotate"]) if "rotate" in params else None
    scale = _scale(params["scale"]) if "scale" in params else None
    if move is None and rotate is None and scale is None:
        raise TransformParamError(
            "transform needs at least one of 'move', 'rotate', 'scale'")
    return {"move": move if move is not None else (0.0, 0.0, 0.0),
            "rotate": rotate, "scale": scale, "copy": bool(params.get("copy", False))}


def _vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector, else TransformParamError."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise TransformParamError(f"transform '{field}' must be an [x, y, z]; got {value!r}")


def _rotate(spec: dict) -> dict:
    """A rotate spec: axis (X/Y/Z or [x,y,z]) + angle (degrees) + about (default origin)."""
    axis_raw = spec.get("axis")
    if isinstance(axis_raw, str) and axis_raw in _AXES:
        axis = _AXES[axis_raw]
    elif isinstance(axis_raw, (list, tuple)) and len(axis_raw) == 3:
        axis = (float(axis_raw[0]), float(axis_raw[1]), float(axis_raw[2]))
    else:
        raise TransformParamError(
            f"transform rotate 'axis' must be X/Y/Z or [x,y,z]; got {axis_raw!r}")
    if "angle" not in spec:
        raise TransformParamError("transform rotate needs an 'angle'")
    about = _vec3(spec["about"], "about") if "about" in spec else (0.0, 0.0, 0.0)
    return {"axis": axis, "angle": float(spec["angle"]), "about": about}


def _scale(value: object):
    """A uniform scale factor or a [sx,sy,sz] tuple; all factors nonzero."""
    if isinstance(value, (int, float)):
        if float(value) == 0.0:
            raise TransformParamError("transform 'scale' must be nonzero")
        return float(value)
    if isinstance(value, (list, tuple)) and len(value) == 3:
        factors = (float(value[0]), float(value[1]), float(value[2]))
        if any(f == 0.0 for f in factors):
            raise TransformParamError("transform 'scale' factors must be nonzero")
        return factors
    raise TransformParamError(
        f"transform 'scale' must be a number or [sx, sy, sz]; got {value!r}")
