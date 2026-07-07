"""Parse and validate a draft feature's vocabulary into a draft description.

A draft names ``faces`` (to taper, resolved by the builder as a face_list ref, not here),
a positive ``angle`` in (0, 90) degrees, and a neutral plane: ``neutral`` in {XY, XZ, YZ}
(default XY) with an optional ``neutral_offset`` along its normal (the plane_offset
convention). A contract violation raises DraftParamError (the op wraps it into a BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)

_PLANES = ("XY", "XZ", "YZ")


class DraftParamError(Exception):
    """A draft's angle or neutral plane is missing or invalid."""


def draft_kwargs(params: dict) -> dict:
    """Return the validated draft description for a draft feature."""
    if "angle" not in params:
        raise DraftParamError("draft needs an 'angle'")
    angle = float(params["angle"])
    if not 0.0 < angle < 90.0:
        raise DraftParamError(
            f"draft 'angle' must be in (0, 90) degrees; got {params['angle']}")
    neutral = str(params.get("neutral", "XY"))
    if neutral not in _PLANES:
        raise DraftParamError(f"draft 'neutral' must be one of {_PLANES}; got {neutral!r}")
    return {"angle": angle, "neutral": neutral,
            "neutral_offset": float(params.get("neutral_offset", 0.0))}
