import pytest

from ncad.params.expression_error import ExpressionError
from ncad.params.function_registry import FunctionRegistry


def test_register_and_get() -> None:
    reg = FunctionRegistry()
    reg.register("double", lambda x: x * 2)

    assert reg.get("double")(3) == 6


def test_unknown_function_raises_expression_error() -> None:
    with pytest.raises(ExpressionError):
        FunctionRegistry().get("nope")


def test_with_defaults_has_min_max_clamp() -> None:
    reg = FunctionRegistry.with_defaults()

    assert reg.get("min")(3, 5) == 3
    assert reg.get("max")(3, 5) == 5
    assert reg.get("clamp")(12, 0, 10) == 10
    assert reg.get("clamp")(-2, 0, 10) == 0
    assert reg.get("clamp")(5, 0, 10) == 5
