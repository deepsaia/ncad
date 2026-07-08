"""One body in a part: a persistent-identity solid (or, later, surface/sheet) shape."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Body:
    """A single body with first-class, persistent identity.

    :ivar id: persistent, feature-derived id (e.g. ``"base/body/0"``), stable across
        rebuilds; never positional. Minted at body birth, preserved through history.
    :ivar kind: ``"solid"`` in bucket 3.0; ``"surface"``/``"sheet"``/``"wire"`` reserved for
        later surfacing/sheet-metal so those slot in with no model rewrite.
    :ivar shape: the kernel-opaque handle for this one body.
    :ivar created_by: the feature id that produced this body (per-body provenance).
    """

    id: str
    kind: str
    shape: Any
    created_by: str
