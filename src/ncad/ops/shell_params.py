"""Parse and validate a shell feature's vocabulary into a shell description.

A shell names a positive ``thickness`` (the wall) and optionally ``openings`` (faces to
remove, resolved by the builder as a face_list ref, not here). A contract violation raises
ShellParamError (the op wraps it into a BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)


class ShellParamError(Exception):
    """A shell's thickness is missing or non-positive."""


def shell_kwargs(params: dict) -> dict:
    """Return the validated shell description for a shell feature.

    Per-face (multi-thickness) shell is NOT supported: OCCT's ``MakeThickSolid`` takes a
    single offset, so genuine per-face wall thicknesses are not achievable on our stack. A
    ``thicknesses`` (per-face) request is refused clearly rather than faked; use a uniform
    ``thickness`` plus ``openings`` (faces to remove).
    """
    if "thicknesses" in params:
        raise ShellParamError(
            "per-face multi-thickness shell is not supported (OCCT MakeThickSolid is "
            "single-offset); use a uniform 'thickness' + 'openings'")
    if "thickness" not in params:
        raise ShellParamError("shell needs a 'thickness'")
    thickness = float(params["thickness"])
    if thickness <= 0.0:
        raise ShellParamError(
            f"shell 'thickness' must be positive; got {params['thickness']}")
    return {"thickness": thickness}
