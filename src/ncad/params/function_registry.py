"""Registry of pure functions callable from parameter expressions (design section 1).

The expression evaluator dispatches ``Call`` nodes here. The library is intentionally
tiny in this bucket (the mechanism matters, not breadth); it grows in code, never in
the document.
"""

from collections.abc import Callable

from ncad.params.expression_error import ExpressionError


class FunctionRegistry:
    """Maps expression function names to pure Python callables."""

    def __init__(self) -> None:
        self._fns: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        """Register ``fn`` under ``name`` for use in expressions."""
        self._fns[name] = fn

    def get(self, name: str) -> Callable:
        """Return the callable for ``name``.

        :raises ExpressionError: If no function is registered under ``name``.
        """
        if name not in self._fns:
            raise ExpressionError(f"unknown function in expression: {name!r}")
        return self._fns[name]

    @classmethod
    def with_defaults(cls) -> "FunctionRegistry":
        """A registry with the bucket 0.2 stub library (min, max, clamp)."""
        reg = cls()
        reg.register("min", min)
        reg.register("max", max)
        reg.register("clamp", _clamp)
        return reg


def _clamp(value: float, low: float, high: float) -> float:
    """Constrain ``value`` to the inclusive range [``low``, ``high``]."""
    return max(low, min(high, value))
