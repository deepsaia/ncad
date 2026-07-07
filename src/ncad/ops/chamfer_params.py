"""Parse and validate a chamfer feature's vocabulary into a chamfer description.

A chamfer names a first ``distance`` (setback) plus at most one variant selector:
``distance2`` (a second setback >> two-distance) or ``angle`` (degrees >> distance-angle,
measured from an auto-picked adjacent face). Neither present is a symmetric chamfer. A
contract violation raises ChamferParamError (the op wraps it into a BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)


class ChamferParamError(Exception):
    """A chamfer's distances or angle are missing, non-positive, or a bad combination."""


def chamfer_kwargs(params: dict) -> dict:
    """Return the validated chamfer description for a chamfer feature."""
    if "distance" not in params:
        raise ChamferParamError("chamfer needs a 'distance'")
    distance = float(params["distance"])
    if distance <= 0.0:
        raise ChamferParamError(
            f"chamfer 'distance' must be positive; got {params['distance']}")
    has_distance2 = "distance2" in params
    has_angle = "angle" in params
    if has_distance2 and has_angle:
        raise ChamferParamError(
            "chamfer cannot be both two-distance (distance2) and distance-angle (angle)")
    distance2 = _positive_or_none(params, "distance2") if has_distance2 else None
    angle = _angle_or_none(params) if has_angle else None
    return {"distance": distance, "distance2": distance2, "angle": angle}


def _positive_or_none(params: dict, key: str) -> float:
    """A positive float field, else ChamferParamError."""
    value = float(params[key])
    if value <= 0.0:
        raise ChamferParamError(f"chamfer '{key}' must be positive; got {params[key]}")
    return value


def _angle_or_none(params: dict) -> float:
    """A chamfer angle in the open interval (0, 90) degrees, else ChamferParamError."""
    value = float(params["angle"])
    if not 0.0 < value < 90.0:
        raise ChamferParamError(
            f"chamfer 'angle' must be in (0, 90) degrees; got {params['angle']}")
    return value
