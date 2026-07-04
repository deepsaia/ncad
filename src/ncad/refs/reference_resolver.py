"""Resolve a Reference to concrete shapes or elements against the current build state.

Semantic feature refs resolve to a prior feature's shape; semantic instance refs and
generative/selector refs resolve to elements of the current working solid. Failures are
returned as data (Resolution.error) for the caller to turn into an id-tagged BuildIssue;
a malformed selector never propagates as an exception.
"""

import logging
from dataclasses import dataclass, field

from ncad.refs.attribute_model import AttributeModel
from ncad.refs.element import Element
from ncad.refs.element_map import ElementMap
from ncad.refs.reference import Reference
from ncad.refs.selector import Selector
from ncad.refs.selector_error import SelectorError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Resolution:
    """The outcome of resolving a Reference."""

    shapes: list = field(default_factory=list)
    elements: list = field(default_factory=list)
    error: str | None = None


class ReferenceResolver:
    """Turns a parsed Reference into shapes/elements or a typed failure."""

    def __init__(self, element_map: ElementMap,
                 attribute_model: AttributeModel | None = None) -> None:
        self._map = element_map
        self._selector = Selector(attribute_model)

    def resolve(self, reference: Reference, feature_shapes: dict,
                current_elements: list[Element]) -> Resolution:
        """Resolve ``reference``; never raises for query problems."""
        if reference.kind == "semantic":
            return self._resolve_semantic(reference, feature_shapes)
        if reference.kind == "generative":
            return self._resolve_generative(reference, current_elements)
        return self._resolve_selector(reference, current_elements)

    def _resolve_semantic(self, reference: Reference, feature_shapes: dict) -> Resolution:
        payload = reference.payload
        if "instance" in payload:
            element = self._map.instance(payload["feature"], payload["instance"])
            if element is None:
                return Resolution(error=f"no instance {payload['instance']} of "
                                        f"{payload['feature']!r}")
            return Resolution(elements=[element])
        feature = payload["feature"]
        if feature in feature_shapes:
            return Resolution(shapes=[feature_shapes[feature]])
        return Resolution(error=f"unresolved semantic reference {reference.text!r}")

    def _resolve_generative(self, reference: Reference,
                            current_elements: list[Element]) -> Resolution:
        feature = reference.payload["feature"]
        tag = reference.payload["tag"]
        matched = [e for e in current_elements
                   if e.tag == tag and e.created_by == feature]
        if not matched:
            return Resolution(error=f"no elements tagged {reference.text!r}")
        return Resolution(elements=matched)

    def _resolve_selector(self, reference: Reference,
                          current_elements: list[Element]) -> Resolution:
        try:
            matched = self._selector.select(reference.payload["query"], current_elements)
        except SelectorError as exc:
            return Resolution(error=str(exc))
        if not matched:
            return Resolution(error=f"selector matched nothing: {reference.text!r}")
        return Resolution(elements=matched)
