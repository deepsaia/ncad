"""Parse and validate a hole feature's wizard vocabulary into a hole description.

A hole names an effective ``diameter`` (explicit, or resolved from ``size`` + ``fit`` via
the ISO table), at most one of ``counterbore`` (diameter + depth) or ``countersink``
(diameter + angle, default 82), and an optional cosmetic ``thread`` tag (metadata only, no
geometry change). A contract violation raises HoleParamError (the op wraps it into a
BuildIssue). Positions / depth / through / on stay in the op (unchanged).
"""

import logging

from ncad.ops.hole_sizes import HoleSizeTable

logger = logging.getLogger(__name__)

_DEFAULT_COUNTERSINK_ANGLE = 82.0


class HoleParamError(Exception):
    """A hole's diameter, sizing, or counterbore/countersink combination is invalid."""


def hole_kwargs(params: dict) -> dict:
    """Return the validated hole description for a hole feature."""
    diameter = _effective_diameter(params)
    has_cbore = "counterbore" in params
    has_csink = "countersink" in params
    if has_cbore and has_csink:
        raise HoleParamError("hole cannot be both counterbore and countersink")
    return {
        "diameter": diameter,
        "counterbore": _counterbore(params["counterbore"]) if has_cbore else None,
        "countersink": _countersink(params["countersink"]) if has_csink else None,
        "thread": str(params["thread"]) if "thread" in params else None,
    }


def _effective_diameter(params: dict) -> float:
    """Explicit ``diameter`` wins; else resolve ``size`` + ``fit``; else error."""
    if "diameter" in params:
        value = float(params["diameter"])
        if value <= 0.0:
            raise HoleParamError(
                f"hole 'diameter' must be positive; got {params['diameter']}")
        return value
    if "size" in params:
        fit = str(params.get("fit", "normal"))
        try:
            return HoleSizeTable().resolve_diameter(str(params["size"]), fit)
        except ValueError as exc:
            raise HoleParamError(str(exc)) from exc
    raise HoleParamError("hole needs a 'diameter' or a 'size' + 'fit'")


def _counterbore(spec: dict) -> dict:
    """A counterbore sub-spec: positive diameter + depth."""
    return {"diameter": _positive(spec, "diameter", "counterbore"),
            "depth": _positive(spec, "depth", "counterbore")}


def _countersink(spec: dict) -> dict:
    """A countersink sub-spec: positive diameter + angle (default 82 degrees)."""
    angle = float(spec.get("angle", _DEFAULT_COUNTERSINK_ANGLE))
    if not 0.0 < angle < 180.0:
        raise HoleParamError(
            f"countersink 'angle' must be in (0, 180); got {spec.get('angle')}")
    return {"diameter": _positive(spec, "diameter", "countersink"), "angle": angle}


def _positive(spec: dict, key: str, owner: str) -> float:
    """A required positive float field of a sub-spec, else HoleParamError."""
    if key not in spec:
        raise HoleParamError(f"{owner} needs a '{key}'")
    value = float(spec[key])
    if value <= 0.0:
        raise HoleParamError(f"{owner} '{key}' must be positive; got {spec[key]}")
    return value
