"""Parse and validate a ``split`` feature's vocabulary.

A split divides the running body by a plane (see plane_spec for the plane vocabulary).
``keep`` is ``both`` (default: two addressable bodies), ``top`` (positive side of the plane
normal), or ``bottom``. A contract violation raises SplitParamError.
"""

import logging

from ncad.ops.plane_spec import PlaneSpecError, parse_plane

logger = logging.getLogger(__name__)

_KEEP = ("both", "top", "bottom")
_TOOL_KEEP = ("both", "inside", "outside")


class SplitParamError(Exception):
    """A split's plane/keep vocabulary is missing or invalid."""


def split_kwargs(params: dict, has_tool: bool = False) -> dict:
    """Return the validated split description: plane (normalized, or None for a tool), keep.

    A plane split needs a ``plane`` (keep both/top/bottom); a tool-body split (``has_tool``)
    has no plane and uses the region ``keep`` vocabulary (both / inside / outside).
    """
    if has_tool:
        keep = params.get("keep", "both")
        if keep not in _TOOL_KEEP:
            raise SplitParamError(
                f"tool-body split 'keep' must be one of {_TOOL_KEEP}; got {keep!r}")
        return {"plane": None, "keep": keep}
    if "plane" not in params:
        raise SplitParamError("split needs a 'plane' (XY/XZ/YZ or {point, normal})")
    try:
        plane = parse_plane(params["plane"], params.get("plane_offset", 0.0))
    except PlaneSpecError as exc:
        raise SplitParamError(str(exc)) from exc
    keep = params.get("keep", "both")
    if keep not in _KEEP:
        raise SplitParamError(f"split 'keep' must be one of {_KEEP}; got {keep!r}")
    return {"plane": plane, "keep": keep}
