"""Parse and validate a feature_pattern feature: an operation + a pattern placement spec.

A feature pattern re-applies a tool-producing feature's effect (a cut or boss) at each pattern
location: it patterns the referenced feature's TOOL solid and applies one boolean. The
placement vocabulary is the body-pattern one (reused from pattern_params). A contract
violation raises FeaturePatternParamError (the op wraps it into an id-tagged issue).
"""

from ncad.ops.pattern_params import PatternParamError, pattern_kwargs

_OPERATIONS = ("cut", "union")


class FeaturePatternParamError(Exception):
    """A feature_pattern operation or placement spec is missing or invalid."""


def feature_pattern_kwargs(params: dict) -> dict:
    """Return ``{operation, pattern}`` for a feature_pattern feature."""
    operation = params.get("operation", "cut")
    if operation not in _OPERATIONS:
        raise FeaturePatternParamError(
            f"feature_pattern 'operation' must be one of {_OPERATIONS}; got {operation!r}")
    try:
        pattern = pattern_kwargs(params)
    except PatternParamError as exc:
        raise FeaturePatternParamError(str(exc)) from exc
    return {"operation": operation, "pattern": pattern}
