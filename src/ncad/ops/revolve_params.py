"""Parse and validate a revolve/groove feature's axis + options into kernel kwargs.

The feature dict names an ``axis`` (``X``/``Y``/``Z``, an arbitrary ``{point, dir}``, or a
reference string, deferred) plus optional ``angle`` (default 360, in ``(0, 360]``),
``symmetric``, and ``thin``. This turns that vocabulary into the keyword args
``Kernel.revolve`` consumes, validating each. Both RevolveOp and GrooveOp use it, so the
vocabulary lives in one place. A contract violation raises RevolveParamError (the op wraps
it into a BuildIssue).

Axis-by-reference (a ``datums.<id>`` datum axis) resolves via the builder into
``refs["axis"]`` as an ``((ox,oy,oz),(dx,dy,dz))`` tuple; a literal X/Y/Z name or
``{point, dir}`` object is resolved here.
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
        raise RevolveParamError("revolve needs an 'axis' (X/Y/Z, {point, dir}, or datums.<id>)")
    # A `datums.<id>` axis resolves (via the builder) to an ((ox,oy,oz),(dx,dy,dz)) tuple in
    # refs["axis"]; a base name / {point, dir} is resolved literally.
    resolved = refs.get("axis")
    if resolved is not None:
        axis_point, axis_dir = resolved
    else:
        axis_point, axis_dir = resolve_axis(params["axis"])
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


def resolve_axis(axis) -> tuple[tuple, tuple]:
    """Resolve a LITERAL axis spec to (point, unit-dir).

    A `datums.<id>` axis reference is resolved earlier (via the builder into refs["axis"]);
    this handles the literal X/Y/Z names and {point, dir} objects.
    """
    if isinstance(axis, str):
        if axis in _NAMED_AXES:
            return (0.0, 0.0, 0.0), _NAMED_AXES[axis]
        raise RevolveParamError(
            f"unknown axis {axis!r}; use X/Y/Z, {{point, dir}}, or a datums.<id> reference")
    if isinstance(axis, dict) and "point" in axis and "dir" in axis:
        point = tuple(float(c) for c in axis["point"])
        dx, dy, dz = (float(c) for c in axis["dir"])
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-12:
            raise RevolveParamError("revolve axis 'dir' must be non-zero")
        return point, (dx / length, dy / length, dz / length)
    raise RevolveParamError(
        f"unknown axis spec {axis!r}; expected X/Y/Z or {{point, dir}}")
