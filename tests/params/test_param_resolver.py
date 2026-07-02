import pytest

from ncad.params.expression_error import ExpressionError
from ncad.params.function_registry import FunctionRegistry
from ncad.params.param_resolver import ParamResolver


def _resolver() -> ParamResolver:
    return ParamResolver(FunctionRegistry.with_defaults())


def test_plain_numbers_pass_through() -> None:
    doc = {"parameters": {"w": 80, "h": 60}, "parts": {}}

    out = _resolver().resolve_document(doc)

    assert out["parameters"] == {"w": 80, "h": 60}


def test_arithmetic_with_precedence_and_parens() -> None:
    doc = {"parameters": {"a": "2 + 3 * 4", "b": "(2 + 3) * 4"}, "parts": {}}

    out = _resolver().resolve_document(doc)

    assert out["parameters"]["a"] == 14
    assert out["parameters"]["b"] == 20


def test_reference_and_chained_reference() -> None:
    doc = {"parameters": {"hole_d": 6, "margin": "${hole_d} * 1.5",
                          "inset": "${margin} + 1"}, "parts": {}}

    out = _resolver().resolve_document(doc)

    assert out["parameters"]["margin"] == 9.0
    assert out["parameters"]["inset"] == 10.0


def test_registered_function_call() -> None:
    doc = {"parameters": {"x": 12, "capped": "clamp(${x}, 0, 10)"}, "parts": {}}

    out = _resolver().resolve_document(doc)

    assert out["parameters"]["capped"] == 10


def test_unknown_reference_raises() -> None:
    doc = {"parameters": {"a": "${missing} + 1"}, "parts": {}}

    with pytest.raises(ExpressionError):
        _resolver().resolve_document(doc)


def test_cycle_raises() -> None:
    doc = {"parameters": {"a": "${b} + 1", "b": "${a} + 1"}, "parts": {}}

    with pytest.raises(ExpressionError):
        _resolver().resolve_document(doc)


def test_disallowed_syntax_raises() -> None:
    doc = {"parameters": {"a": "__import__('os').getcwd()"}, "parts": {}}

    with pytest.raises(ExpressionError):
        _resolver().resolve_document(doc)


def test_feature_field_expressions_are_inlined() -> None:
    doc = {
        "parameters": {"t": 8},
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": "${t}"},
        ]}},
    }

    out = _resolver().resolve_document(doc)

    assert out["parts"]["p"]["features"][0]["distance"] == 8


def test_expression_inside_nested_list_is_inlined() -> None:
    doc = {
        "parameters": {"m": 9},
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "h", "op": "hole", "positions": [["${m}", "${m}"]]},
        ]}},
    }

    out = _resolver().resolve_document(doc)

    assert out["parts"]["p"]["features"][0]["positions"] == [[9, 9]]
