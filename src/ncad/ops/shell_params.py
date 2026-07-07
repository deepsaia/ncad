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
    """Return the validated shell description for a shell feature."""
    if "thickness" not in params:
        raise ShellParamError("shell needs a 'thickness'")
    thickness = float(params["thickness"])
    if thickness <= 0.0:
        raise ShellParamError(
            f"shell 'thickness' must be positive; got {params['thickness']}")
    return {"thickness": thickness}
