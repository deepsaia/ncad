"""Parse and validate a ``boolean`` feature's vocabulary into a combine description.

Two modes. Ref mode combines prior-feature refs: a ``target`` plus exactly one of ``tool``
(single) or ``tools`` (a list). Scope mode combines bodies of the running multibody shape,
named by born-once id in ``scope`` (a nonempty ordered list); it takes no target/tool.
``operation`` is cut/union/intersect (default cut). ``merge`` (default true) keeps the 3.0
keep-separate behavior for a union when false. A contract violation raises BooleanParamError.
"""

import logging

logger = logging.getLogger(__name__)

_OPERATIONS = ("cut", "union", "intersect")


class BooleanParamError(Exception):
    """A boolean's operation/mode vocabulary is missing, ambiguous, or invalid."""


def boolean_kwargs(params: dict) -> dict:
    """Return the validated boolean description: operation, mode, merge, scope."""
    operation = params.get("operation", "cut")
    if operation not in _OPERATIONS:
        raise BooleanParamError(f"boolean 'operation' must be one of {_OPERATIONS}; "
                                f"got {operation!r}")
    merge = bool(params.get("merge", True))
    has_scope = "scope" in params
    has_tool = "tool" in params
    has_tools = "tools" in params
    if has_scope:
        if has_tool or has_tools:
            raise BooleanParamError(
                "boolean 'scope' mode takes no 'tool'/'tools' (it combines running bodies)")
        scope = params["scope"]
        # scope is a nonempty list of born-once body ids, OR a `select bodies where ...`
        # Selector query string the op resolves against the running BodySet.
        if isinstance(scope, str) and scope.strip().lower().startswith("select bodies"):
            return {"operation": operation, "mode": "scope", "merge": merge,
                    "scope": None, "scope_query": scope}
        if not isinstance(scope, list) or not scope or not all(
                isinstance(s, str) for s in scope):
            raise BooleanParamError(
                "boolean 'scope' must be a nonempty list of body ids or a "
                "'select bodies where ...' query")
        return {"operation": operation, "mode": "scope", "merge": merge, "scope": list(scope),
                "scope_query": None}
    # ref mode: needs exactly one of tool / tools.
    if has_tool and has_tools:
        raise BooleanParamError("boolean names both 'tool' and 'tools'; use one")
    if not has_tool and not has_tools:
        raise BooleanParamError("boolean ref mode needs a 'tool' or 'tools' (or use 'scope')")
    return {"operation": operation, "mode": "ref", "merge": merge, "scope": None,
            "scope_query": None}
