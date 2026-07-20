"""A typed reference to geometry: semantic, generative, or selector.

Parsing picks the kind from the surface form. The resolver
(see reference_resolver.py) turns a Reference into concrete elements/shapes at
build time. No topology or randomness here: parsing is pure.
"""

import re

_INSTANCE = re.compile(r"^([A-Za-z_]\w*)\.instance\((\d+)\)$")
_GENERATIVE = re.compile(r"^([A-Za-z_]\w*)\.([A-Za-z_]\w*(?:\([^)]*\))?)$")


class Reference:
    """A parsed reference. ``kind`` is 'semantic' | 'generative' | 'selector'."""

    def __init__(self, kind: str, text: str, payload: dict) -> None:
        self.kind = kind
        self.text = text
        self.payload = payload

    @classmethod
    def parse(cls, text: str) -> "Reference":
        """Parse ``text`` into a typed Reference (pure; never raises)."""
        stripped = text.strip()
        if stripped[:7].lower() == "select ":
            return cls("selector", text, {"query": text})
        instance = _INSTANCE.match(stripped)
        if instance is not None:
            return cls("semantic", text,
                       {"feature": instance.group(1), "instance": int(instance.group(2))})
        generative = _GENERATIVE.match(stripped)
        if generative is not None and generative.group(1) != "datums":
            return cls("generative", text,
                       {"feature": generative.group(1), "tag": generative.group(2)})
        return cls("semantic", text, {"feature": stripped})
