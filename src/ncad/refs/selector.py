"""Parse and evaluate a selector query over element attributes (design section 2).

Grammar (lark): ``select (edges|faces|vertices) where <predicate>``. The predicate
is comparisons of ``attr OP literal`` joined by ``and``/``or`` and parenthesizable.
Evaluation is a pure walk over each element's ``attrs`` dict. A malformed query or an
attribute outside the AttributeModel raises SelectorError.
"""

import logging
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from ncad.refs.attribute_model import AttributeModel
from ncad.refs.selector_error import SelectorError

logger = logging.getLogger(__name__)

_GRAMMAR = r"""
    start: "select" COLLECTION "where" predicate
    COLLECTION: "edges" | "faces" | "vertices"
    ?predicate: or_expr
    ?or_expr: and_expr ("or" and_expr)*      -> or_node
    ?and_expr: atom ("and" atom)*            -> and_node
    ?atom: comparison
         | "(" predicate ")"
    comparison: NAME OP value
    OP: "!=" | "<=" | ">=" | "=" | "<" | ">"
    value: ESCAPED_SINGLE | SIGNED_NUMBER
    ESCAPED_SINGLE: /'[^']*'/
    NAME: /[a-zA-Z_]\w*/
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""

_COLLECTION_KIND = {"edges": "edge", "faces": "face", "vertices": "vertex"}


class Selector:
    """Compiles a selector query and filters a list of elements by it."""

    def __init__(self, attribute_model: AttributeModel | None = None) -> None:
        self._attrs = attribute_model or AttributeModel()
        self._parser = Lark(_GRAMMAR, parser="earley")

    def select(self, text: str, elements: list) -> list:
        """Return the elements matching ``text``. Raises SelectorError on bad query."""
        try:
            tree = self._parser.parse(text)
        except LarkError as exc:
            raise SelectorError(f"invalid selector {text!r}: {exc}") from exc
        collection = str(tree.children[0])
        kind = _COLLECTION_KIND[collection]
        predicate = tree.children[1]
        self._check_attributes(predicate)
        return [e for e in elements if e.kind == kind and self._eval(predicate, e)]

    def _check_attributes(self, node: Any) -> None:
        """Raise SelectorError for any attribute name outside the AttributeModel."""
        if isinstance(node, Tree) and node.data == "comparison":
            name = str(node.children[0])
            if not self._attrs.is_known(name):
                raise SelectorError(f"unknown attribute {name!r}")
            return
        if isinstance(node, Tree):
            for child in node.children:
                self._check_attributes(child)

    def _eval(self, node: Any, element: Any) -> bool:
        """Evaluate a predicate node against one element's attrs."""
        if isinstance(node, Tree) and node.data == "or_node":
            return any(self._eval(c, element) for c in node.children)
        if isinstance(node, Tree) and node.data == "and_node":
            return all(self._eval(c, element) for c in node.children)
        if isinstance(node, Tree) and node.data == "comparison":
            return self._compare(node, element)
        raise SelectorError(f"unexpected selector node {node!r}")

    def _compare(self, node: Any, element: Any) -> bool:
        """Evaluate a single ``attr OP literal`` comparison."""
        name = str(node.children[0])
        op = str(node.children[1])
        literal = self._literal(node.children[2])
        actual = element.attrs.get(name)
        if actual is None:
            return False
        return _apply_op(op, actual, literal)

    @staticmethod
    def _literal(value_node: Any) -> Any:
        """Extract a string or numeric literal from a ``value`` node."""
        token = value_node.children[0] if isinstance(value_node, Tree) else value_node
        text = str(token)
        if isinstance(token, Token) and token.type == "ESCAPED_SINGLE":
            return text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            return text[1:-1]
        return float(text)


def _apply_op(op: str, actual: Any, literal: Any) -> bool:
    """Apply a comparison operator, coercing to float when the literal is numeric."""
    if isinstance(literal, float) and not isinstance(actual, str):
        actual = float(actual)
    if op == "=":
        return actual == literal
    if op == "!=":
        return actual != literal
    if op == "<":
        return actual < literal
    if op == ">":
        return actual > literal
    if op == "<=":
        return actual <= literal
    if op == ">=":
        return actual >= literal
    raise SelectorError(f"unknown operator {op!r}")
