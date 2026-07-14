"""Parse and validate a feature_mirror feature: an operation + a mirror plane.

A feature mirror re-applies a tool-producing feature's effect (a cut or boss) reflected across
a plane: it reflects the referenced feature's TOOL solid and applies one boolean. The plane
vocabulary is the mirror one (a base string / {point, normal} object, or a referenced planar
FACE), reused from mirror_params. A contract violation raises FeatureMirrorParamError.
"""

from ncad.ops.mirror_params import MirrorParamError, mirror_kwargs

_OPERATIONS = ("cut", "union")


class FeatureMirrorParamError(Exception):
    """A feature_mirror operation or mirror plane is missing or invalid."""


def feature_mirror_kwargs(params: dict, refs: dict) -> dict:
    """Return ``{operation, plane}`` for a feature_mirror feature."""
    operation = params.get("operation", "cut")
    if operation not in _OPERATIONS:
        raise FeatureMirrorParamError(
            f"feature_mirror 'operation' must be one of {_OPERATIONS}; got {operation!r}")
    try:
        # mirror_kwargs validates + normalizes the plane (base / {point,normal} / face ref).
        plane = mirror_kwargs(params, refs)["plane"]
    except MirrorParamError as exc:
        raise FeatureMirrorParamError(str(exc)) from exc
    return {"operation": operation, "plane": plane}
