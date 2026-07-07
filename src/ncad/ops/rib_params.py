"""Parse and validate a rib feature's vocabulary into a rib description.

A rib names a ``profile`` (an open sketch wire) and a ``target`` solid, plus a positive
``thickness`` (symmetric about the profile curve) and ``depth`` (growth normal to the
sketch plane). A contract violation raises RibParamError (the op wraps it into a
BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)


class RibParamError(Exception):
    """A rib's thickness or depth is missing or non-positive."""


def rib_kwargs(params: dict, refs: dict) -> dict:
    """Return the validated rib description for a rib feature."""
    return {"thickness": _positive(params, "thickness"),
            "depth": _positive(params, "depth")}


def _positive(params: dict, key: str) -> float:
    """A required positive float feature field, else RibParamError."""
    if key not in params:
        raise RibParamError(f"rib needs a '{key}'")
    value = float(params[key])
    if value <= 0.0:
        raise RibParamError(f"rib '{key}' must be positive; got {params[key]}")
    return value
