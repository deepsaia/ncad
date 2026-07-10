"""Parse and validate a ``mirror`` feature's vocabulary into a placement description.

A mirror reflects the running body/bodies across a plane (see plane_spec for the plane
vocabulary). ``keep`` (default true) keeps the original and adds the reflected copy;
``merge`` (default true) fuses the two to one solid. A contract violation raises
MirrorParamError (the op wraps it into a BuildIssue).
"""

import logging

from ncad.ops.plane_spec import PlaneSpecError, parse_plane

logger = logging.getLogger(__name__)


class MirrorParamError(Exception):
    """A mirror's plane/keep/merge vocabulary is missing or invalid."""


def mirror_kwargs(params: dict) -> dict:
    """Return the validated mirror description: plane (normalized), keep, merge."""
    if "plane" not in params:
        raise MirrorParamError("mirror needs a 'plane' (XY/XZ/YZ or {point, normal})")
    try:
        plane = parse_plane(params["plane"], params.get("plane_offset", 0.0))
    except PlaneSpecError as exc:
        raise MirrorParamError(str(exc)) from exc
    return {"plane": plane,
            "keep": bool(params.get("keep", True)),
            "merge": bool(params.get("merge", True))}
