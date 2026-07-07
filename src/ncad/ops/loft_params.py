"""Parse and validate a loft feature's vocabulary into a loft description.

A loft names an ordered list of ``sections`` (references to prior sketch profiles) and
options: ``ruled`` (straight vs smooth blend) and optional ``start_point``/``end_point``
vertex caps ([x, y, z]) that make a cone-like end. A loft needs at least 2 total sections
counting caps. A contract violation raises LoftParamError (the op wraps it into a
BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)


class LoftParamError(Exception):
    """A loft's point cap or section count is invalid."""


def loft_kwargs(params: dict, refs: dict) -> dict:
    """Return the validated loft description for a loft feature."""
    start_point = _resolve_point(params.get("start_point"), "start_point")
    end_point = _resolve_point(params.get("end_point"), "end_point")
    section_count = len(refs.get("sections", []))
    total = section_count + (start_point is not None) + (end_point is not None)
    if total < 2:
        raise LoftParamError(
            f"loft needs at least 2 sections (counting point caps); got {total}")
    return {"ruled": bool(params.get("ruled", False)),
            "start_point": start_point, "end_point": end_point}


def _resolve_point(value, field: str):
    """A vertex cap coordinate: None, or an [x, y, z] parsed to a float tuple."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise LoftParamError(f"loft {field} must be an [x, y, z] point; got {value!r}")
