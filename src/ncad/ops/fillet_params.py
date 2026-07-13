"""Parse and validate a fillet feature's radius vocabulary into kernel kwargs.

A fillet is either CONSTANT (a single ``radius``) or VARIABLE (a ``radius_start`` >>
``radius_end`` ramp along each edge, the NX/Creo/Fusion variable-radius fillet). Exactly one
form must be fully specified; a half-specified variable fillet (only one endpoint) is a
contract error. Raises FilletParamError (the op wraps it into an id-tagged issue).
"""


class FilletParamError(Exception):
    """A fillet radius spec is missing or half-specified."""


def fillet_kwargs(params: dict) -> dict:
    """Return ``{variable, radius}`` or ``{variable, radius_start, radius_end}``."""
    has_start = "radius_start" in params
    has_end = "radius_end" in params
    if has_start or has_end:
        if not (has_start and has_end):
            raise FilletParamError(
                "a variable fillet needs both radius_start and radius_end")
        return {"variable": True, "radius_start": float(params["radius_start"]),
                "radius_end": float(params["radius_end"])}
    if "radius" not in params:
        raise FilletParamError(
            "fillet needs a 'radius' (constant) or 'radius_start' + 'radius_end' (variable)")
    return {"variable": False, "radius": float(params["radius"])}
