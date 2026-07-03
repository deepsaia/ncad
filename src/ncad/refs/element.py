"""A single topological element (face/edge/vertex) with queryable attributes.

Produced by ElementMap from a kernel descriptor. ``attrs`` is the flat dict a
Selector queries; ``handle`` is the opaque kernel shape an op acts on.
"""


class Element:
    """One face, edge, or vertex with provenance, an optional generative tag, and attrs."""

    def __init__(self, id: str, kind: str, created_by: str, tag: str | None,
                 attrs: dict, handle: object) -> None:
        self.id = id
        self.kind = kind
        self.created_by = created_by
        self.tag = tag
        self.attrs = attrs
        self.handle = handle
