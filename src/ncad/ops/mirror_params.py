"""Parse and validate a ``mirror`` feature's vocabulary into a placement description.

A mirror reflects the running body/bodies across a plane. ``plane`` is a base plane
(``XY``/``XZ``/``YZ``, optionally shifted by ``plane_offset``) or an arbitrary
``{point, normal}`` object. ``keep`` (default true) keeps the original and adds the
reflected copy (symmetry); ``merge`` (default true) fuses the two to one solid. A contract
violation raises MirrorParamError (the op wraps it into a BuildIssue).

The kernel names a plane's normal ``z_dir``; this module maps the authored ``normal`` to
``z_dir`` so the kernel boundary stays in build123d's vocabulary.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_BASE_PLANES = ("XY", "XZ", "YZ")


class MirrorParamError(Exception):
    """A mirror's plane/keep/merge vocabulary is missing or invalid."""


def mirror_kwargs(params: dict) -> dict:
    """Return the validated mirror description: plane (normalized), keep, merge."""
    if "plane" not in params:
        raise MirrorParamError("mirror needs a 'plane' (XY/XZ/YZ or {point, normal})")
    plane = _plane(params["plane"], params.get("plane_offset", 0.0))
    return {"plane": plane,
            "keep": bool(params.get("keep", True)),
            "merge": bool(params.get("merge", True))}


def _plane(value: object, offset: Any) -> dict:
    """Normalize a base-plane string or a {point, normal} object."""
    if isinstance(value, str):
        if value not in _BASE_PLANES:
            raise MirrorParamError(
                f"mirror 'plane' must be one of {_BASE_PLANES} or an object; got {value!r}")
        return {"kind": "base", "plane": value, "offset": float(offset)}
    if isinstance(value, dict):
        point = _vec3(value["point"], "plane.point") if "point" in value else (0.0, 0.0, 0.0)
        z_dir = _nonzero_vec3(value.get("normal"), "plane.normal")
        return {"kind": "custom", "point": point, "z_dir": z_dir}
    raise MirrorParamError(
        f"mirror 'plane' must be a base-plane string or {{point, normal}}; got {value!r}")


def _vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector, else MirrorParamError."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise MirrorParamError(f"mirror '{field}' must be an [x, y, z]; got {value!r}")


def _nonzero_vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector with nonzero length."""
    vec = _vec3(value, field)
    if vec == (0.0, 0.0, 0.0):
        raise MirrorParamError(f"mirror '{field}' must be nonzero")
    return vec
