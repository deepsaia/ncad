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
    """Return the validated draft description for a draft feature.

    A single ``angle`` tapers all faces; a per-face ``angles`` list (parallel to the resolved
    faces) makes a variable draft, each wall by its own angle. Exactly one form is used.
    """
    angles = params.get("angles")
    if angles is not None:
        angles = [float(a) for a in angles]
        for a in angles:
            if not 0.0 < a < 90.0:
                raise DraftParamError(
                    f"draft 'angles' must each be in (0, 90) degrees; got {a}")
        angle = 0.0
    else:
        if "angle" not in params:
            raise DraftParamError("draft needs an 'angle' (or a per-face 'angles' list)")
        angle = float(params["angle"])
        if not 0.0 < angle < 90.0:
            raise DraftParamError(
                f"draft 'angle' must be in (0, 90) degrees; got {params['angle']}")
    neutral = str(params.get("neutral", "XY"))
    if neutral not in _PLANES:
        raise DraftParamError(f"draft 'neutral' must be one of {_PLANES}; got {neutral!r}")
    return {"angle": angle, "angles": angles, "neutral": neutral,
            "neutral_offset": float(params.get("neutral_offset", 0.0))}
