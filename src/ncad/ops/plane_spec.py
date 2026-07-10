"""Shared parse/normalize for a mirror/split plane vocabulary.

A plane is a base plane (``XY``/``XZ``/``YZ``, optionally shifted by an offset) or an
arbitrary ``{point, normal}`` object. The normalized form is consumed by the kernel:
``{"kind":"base","plane":str,"offset":float}`` or
``{"kind":"custom","point":(x,y,z),"z_dir":(x,y,z)}``. The kernel names a plane's normal
``z_dir``; this maps the authored ``normal`` to ``z_dir`` at the boundary.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_BASE_PLANES = ("XY", "XZ", "YZ")


class PlaneSpecError(Exception):
    """A plane vocabulary (base string or {point, normal}) is missing or invalid."""


def parse_plane(value: object, offset: Any) -> dict:
    """Normalize a base-plane string (+ offset) or a {point, normal} object."""
    if isinstance(value, str):
        if value not in _BASE_PLANES:
            raise PlaneSpecError(
                f"'plane' must be one of {_BASE_PLANES} or an object; got {value!r}")
        return {"kind": "base", "plane": value, "offset": float(offset)}
    if isinstance(value, dict):
        point = _vec3(value["point"], "plane.point") if "point" in value else (0.0, 0.0, 0.0)
        z_dir = _nonzero_vec3(value.get("normal"), "plane.normal")
        return {"kind": "custom", "point": point, "z_dir": z_dir}
    raise PlaneSpecError(
        f"'plane' must be a base-plane string or {{point, normal}}; got {value!r}")


def _vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector, else PlaneSpecError."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise PlaneSpecError(f"'{field}' must be an [x, y, z]; got {value!r}")


def _nonzero_vec3(value: object, field: str) -> tuple[float, float, float]:
    """A 3-number vector with nonzero length."""
    vec = _vec3(value, field)
    if vec == (0.0, 0.0, 0.0):
        raise PlaneSpecError(f"'{field}' must be nonzero")
    return vec
