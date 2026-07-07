"""Parse and validate a revolve/groove feature's axis + options into kernel kwargs.

The feature dict names an ``axis`` (``X``/``Y``/``Z``, an arbitrary ``{point, dir}``, or a
reference string, deferred) plus optional ``angle`` (default 360, in ``(0, 360]``),
``symmetric``, and ``thin``. This turns that vocabulary into the keyword args
``Kernel.revolve`` consumes, validating each. Both RevolveOp and GrooveOp use it, so the
vocabulary lives in one place. A contract violation raises RevolveParamError (the op wraps
it into a BuildIssue).

Axis-by-reference (a datum axis or a sketch line) is accepted by the field shape but not
yet resolvable: datums do not exist in the codebase yet, so a reference string raises a
clear deferral error rather than silently doing the wrong thing.
"""

import logging
import math

logger = logging.getLogger(__name__)

_NAMED_AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


class RevolveParamError(Exception):
    """A revolve/groove axis or option is unknown, malformed, or out of range."""


def revolve_kwargs(params: dict, refs: dict) -> dict:
    """Return the ``Kernel.revolve`` keyword args for a revolve/groove feature."""
    if "axis" not in params:
        raise RevolveParamError("revolve needs an 'axis' (X/Y/Z or {point, dir})")
    axis_point, axis_dir = _resolve_axis(params["axis"])
    angle = float(params.get("angle", 360.0))
    if not 0.0 < angle <= 360.0:
        raise RevolveParamError(f"revolve angle must be in (0, 360]; got {angle}")
    kwargs: dict = {"axis_point": axis_point, "axis_dir": axis_dir, "angle": angle,
                    "symmetric": bool(params.get("symmetric", False))}
    if "thin" in params:
        thin = float(params["thin"])
        if thin <= 0.0:
            raise RevolveParamError(f"revolve thin wall must be positive; got {thin}")
        kwargs["thin"] = thin
    return kwargs


def _resolve_axis(axis) -> tuple[tuple, tuple]:
    """Resolve an axis spec to (point, unit-dir). Reference strings are deferred."""
    if isinstance(axis, str):
        if axis in _NAMED_AXES:
            return (0.0, 0.0, 0.0), _NAMED_AXES[axis]
        raise RevolveParamError(
            f"axis references not yet supported; use X/Y/Z or {{point, dir}} (got {axis!r})")
    if isinstance(axis, dict) and "point" in axis and "dir" in axis:
        point = tuple(float(c) for c in axis["point"])
        dx, dy, dz = (float(c) for c in axis["dir"])
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-12:
            raise RevolveParamError("revolve axis 'dir' must be non-zero")
        return point, (dx / length, dy / length, dz / length)
    raise RevolveParamError(
        f"unknown axis spec {axis!r}; expected X/Y/Z or {{point, dir}}")
