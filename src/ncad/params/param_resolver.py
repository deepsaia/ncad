"""Resolve a document's parameters and inline every ``${...}`` expression.

Runs before the build. An expression is a string containing one or
more ``${name}`` references and/or arithmetic and/or calls to registered functions. The
evaluator is a restricted AST walker: only literals, references, +-*/ arithmetic, unary
minus, and registered function calls are allowed; anything else raises ExpressionError.
Parameters may reference each other and are resolved in dependency order.
"""

import ast
import copy
import logging
import re

from ncad.params.expression_error import ExpressionError
from ncad.params.function_registry import FunctionRegistry

logger = logging.getLogger(__name__)

_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


class ParamResolver:
    """Resolves parameters and inlines ``${...}`` expressions throughout a document."""

    def __init__(self, registry: FunctionRegistry) -> None:
        """:param registry: Function registry backing expression ``Call`` nodes."""
        self._registry = registry

    def resolve_document(self, document: dict) -> dict:
        """Return a deep copy with parameters numeric and every expression inlined.

        :raises ExpressionError: On unknown refs, cycles, disallowed syntax, or unknown
            functions.
        """
        out = copy.deepcopy(document)
        params = self._resolve_parameters(out.get("parameters", {}))
        out["parameters"] = params
        if "parts" in out:
            out["parts"] = self._resolve_tree(out["parts"], params)
        return out

    def resolve_value(self, value, params: dict):
        """Resolve a single value (a ``${...}`` expression string, or pass-through)."""
        if isinstance(value, str) and _is_expression(value):
            return self._eval(value, params)
        return value

    def _resolve_parameters(self, raw: dict) -> dict:
        """Resolve the parameters map in dependency order (cycle -> ExpressionError).

        A parameter that is a string is an equation (evaluated even without a ref); a
        number passes through.
        """
        resolved: dict = {}
        pending = dict(raw)
        while pending:
            progressed = False
            for name in list(pending):
                value = pending[name]
                refs = _refs_in(value)
                if all(r in resolved for r in refs):
                    resolved[name] = (
                        self._eval(value, resolved) if isinstance(value, str) else value
                    )
                    del pending[name]
                    progressed = True
            if not progressed:
                raise ExpressionError(
                    f"cannot resolve parameters (cycle or unknown ref): {sorted(pending)}"
                )
        return resolved

    def _resolve_tree(self, node, params: dict):
        """Recursively inline ``${...}`` expressions in dicts/lists/scalars."""
        if isinstance(node, dict):
            return {k: self._resolve_tree(v, params) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve_tree(v, params) for v in node]
        return self.resolve_value(node, params)

    def _eval(self, expr: str, params: dict):
        """Substitute refs, parse, and evaluate a restricted arithmetic expression."""
        substituted = _REF.sub(lambda m: _param_token(m.group(1), params), expr)
        try:
            tree = ast.parse(substituted, mode="eval")
        except SyntaxError as exc:
            raise ExpressionError(f"invalid expression {expr!r}: {exc}") from exc
        return self._eval_node(tree.body, expr)

    def _eval_node(self, node, expr: str):
        """Evaluate one allowed AST node; raise ExpressionError for anything else."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ExpressionError(f"only numbers allowed in expression {expr!r}")
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
            left = self._eval_node(node.left, expr)
            right = self._eval_node(node.right, expr)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            operand = self._eval_node(node.operand, expr)
            return -operand if isinstance(node.op, ast.USub) else operand
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ExpressionError(f"invalid call in expression {expr!r}")
            fn = self._registry.get(node.func.id)
            args = [self._eval_node(a, expr) for a in node.args]
            return fn(*args)
        raise ExpressionError(
            f"disallowed syntax in expression {expr!r}: {type(node).__name__}"
        )


def _is_expression(value: str) -> bool:
    """A string is an expression (in the feature tree) if it contains a ``${...}`` ref."""
    return bool(_REF.search(value))


def _refs_in(value) -> set:
    """Names referenced by a parameter value (empty for plain numbers)."""
    if isinstance(value, str):
        return set(_REF.findall(value))
    return set()


def _param_token(name: str, params: dict) -> str:
    """Substitution text for ``${name}``: the resolved numeric value, or raise."""
    if name not in params:
        raise ExpressionError(f"unknown parameter reference: {name!r}")
    return repr(params[name])
