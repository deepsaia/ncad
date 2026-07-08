"""Parse and validate an extrude/pocket feature's end-condition into kernel kwargs.

The feature dict names an ``end`` (blind/symmetric/two_side/through_all/to_next/to_face/
to_surface, default blind) plus optional ``distance``/``second_distance``/``draft``/
``thin`` and a resolved ``to`` target (for to_face/to_surface). This turns that authored
vocabulary into the keyword args ``Kernel.extrude`` consumes, validating required fields
per end-condition. Both ExtrudeOp and PocketOp use it, so the vocabulary lives in one
place. A contract violation raises ExtrudeParamError (the op wraps it into a BuildIssue).
"""

import logging

logger = logging.getLogger(__name__)

# end -> the build123d Until token it maps to (absent means distance/both, not until).
_UNTIL = {"through_all": "last", "to_next": "next"}
_KNOWN_ENDS = frozenset(
    {"blind", "symmetric", "two_side", "through_all", "to_next", "to_face", "to_surface"})


class ExtrudeParamError(Exception):
    """An extrude/pocket end-condition is unknown or missing a required field."""


def extrude_kwargs(params: dict, refs: dict) -> dict:
    """Return the ``Kernel.extrude`` keyword args for a feature's end-condition."""
    end = params.get("end", "blind")
    if end not in _KNOWN_ENDS:
        raise ExtrudeParamError(
            f"unknown extrude end {end!r}; expected one of {sorted(_KNOWN_ENDS)}")
    # The end-condition is chosen by `end` (e.g. end = symmetric), not by bare boolean
    # flags. Reject a `symmetric`/`two_side` field that does not match `end` so an intuitive
    # but wrong `symmetric = true` fails loudly instead of silently building a blind extrude.
    if "symmetric" in params and end != "symmetric":
        raise ExtrudeParamError(
            "extrude 'symmetric' is selected by end = symmetric, not a 'symmetric' field")
    if "second_distance" in params and end != "two_side":
        raise ExtrudeParamError(
            "extrude 'second_distance' requires end = two_side")
    kwargs: dict = {"draft": float(params.get("draft", 0.0))}
    if "thin" in params:
        kwargs["thin"] = float(params["thin"])
    if end in ("blind", "symmetric", "two_side"):
        if "distance" not in params:
            raise ExtrudeParamError(f"extrude end {end!r} needs a 'distance'")
        kwargs["distance"] = float(params["distance"])
    if end == "symmetric":
        kwargs["symmetric"] = True
    if end == "two_side":
        if "second_distance" not in params:
            raise ExtrudeParamError("extrude end 'two_side' needs a 'second_distance'")
        kwargs["second_distance"] = float(params["second_distance"])
    if end in _UNTIL:
        kwargs["until"] = _UNTIL[end]
    if end in ("to_face", "to_surface"):
        target = refs.get("to")
        if target is None:
            raise ExtrudeParamError(f"extrude end {end!r} needs a resolved 'to' target")
        kwargs["target"] = target
    return kwargs
