"""Parameter parsing for the ``reposition_hole`` direct op."""

from typing import Any


class RepositionHoleParamError(ValueError):
    """A reposition_hole feature's parameters are malformed."""


def reposition_hole_kwargs(params: dict) -> dict[str, Any]:
    """Validate and normalize reposition_hole params into kwargs.

    Requires a ``to`` target position: a 2-tuple ``[u, v]`` in the drilling plane's in-plane
    coordinates (the same convention as ``hole.positions``), matching where the hole should move.
    """
    to = params.get("to")
    if to is None or not isinstance(to, (list, tuple)) or len(to) != 2:
        raise RepositionHoleParamError(
            "reposition_hole needs a 'to' target position [u, v] in the drilling plane")
    try:
        target = (float(to[0]), float(to[1]))
    except (TypeError, ValueError) as exc:
        raise RepositionHoleParamError(f"reposition_hole 'to' must be numeric: {exc}") from exc
    return {"to": target}
