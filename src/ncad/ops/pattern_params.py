"""Parse and validate a ``pattern`` feature's vocabulary into a placement description.

A pattern replicates the running body/bodies. ``kind`` is ``linear`` (a grid, one or two
directions) or ``circular`` (a polar array about an axis). ``merge`` (default true) fuses
the instances to one body; false keeps them as separate bodies. A contract violation
raises PatternParamError (the op wraps it into a BuildIssue).

Note: this feature-level ``pattern`` op is distinct from the sketch-level ``pattern``
transform (``src/ncad/sketch/transform_applier.py``), which replicates 2D sketch entities
before solving and is discriminated by its ``sources`` field. Different layer, different
namespace; both mirror how Fusion separates sketch patterns from feature/body patterns.
"""

import logging

logger = logging.getLogger(__name__)

_DEFAULT_AXIS_DIR = (0.0, 0.0, 1.0)   # +Z, the usual rotation axis
_DEFAULT_AXIS_POINT = (0.0, 0.0, 0.0)


class PatternParamError(Exception):
    """A pattern's kind/linear/circular vocabulary is missing or invalid."""


def pattern_kwargs(params: dict) -> dict:
    """Return the validated placement description for a pattern feature."""
    kind = params.get("kind")
    merge = bool(params.get("merge", True))
    if kind == "linear":
        return {"kind": "linear", "merge": merge, "linear": _linear(params)}
    if kind == "circular":
        return {"kind": "circular", "merge": merge, "circular": _circular(params)}
    raise PatternParamError(
        f"pattern 'kind' must be 'linear' or 'circular'; got {kind!r}")


def _linear(params: dict) -> dict:
    """The linear grid spec: required ``x`` axis, optional ``y`` axis for a 2D grid."""
    if "x" not in params:
        raise PatternParamError("linear pattern needs an 'x' axis {dir, spacing, count}")
    x = _axis_step(params["x"], "x")
    y = _axis_step(params["y"], "y") if "y" in params else None
    return {"x": x, "y": y}


def _axis_step(spec: dict, field: str) -> dict:
    """One linear direction: nonzero dir, nonzero spacing, integer count >= 1."""
    direction = _nonzero_vec3(spec.get("dir"), f"{field}.dir")
    if "spacing" not in spec:
        raise PatternParamError(f"linear pattern '{field}' needs a 'spacing'")
    spacing = float(spec["spacing"])
    if spacing == 0.0:
        raise PatternParamError(f"linear pattern '{field}' spacing must be nonzero")
    return {"dir": direction, "spacing": spacing, "count": _count(spec.get("count"), field)}


def _circular(params: dict) -> dict:
    """The circular spec: count, optional axis {point, dir=+Z}, angle (default 360), rotate."""
    axis = params.get("axis", {})
    point = _vec3(axis["point"], "axis.point") if "point" in axis else _DEFAULT_AXIS_POINT
    direction = (_nonzero_vec3(axis["dir"], "axis.dir")
                 if "dir" in axis else _DEFAULT_AXIS_DIR)
    angle = float(params.get("angle", 360.0))
    if angle <= 0.0:
        raise PatternParamError("circular pattern 'angle' must be > 0")
    return {"axis": {"point": point, "dir": direction},
            "count": _count(params.get("count"), "circular"),
            "angle": angle, "rotate": bool(params.get("rotate", True))}


def _count(value: object, field: str) -> int:
    """An integer instance count >= 1 (count includes the seed)."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise PatternParamError(f"pattern '{field}' count must be an integer >= 1; got {value!r}")
    return value


def _vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector, else PatternParamError."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise PatternParamError(f"pattern '{field}' must be an [x, y, z]; got {value!r}")


def _nonzero_vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector with nonzero length."""
    vec = _vec3(value, field)
    if vec == (0.0, 0.0, 0.0):
        raise PatternParamError(f"pattern '{field}' must be nonzero")
    return vec
