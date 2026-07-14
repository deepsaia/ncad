"""The versioned set of element attributes a selector may query (design section 14).

Only attributes the kernel computes reliably in bucket 0.3 are included. The set is
versioned so existing selectors keep meaning as it grows. ``convexity``, adjacency,
and tangency are deferred (documented, not silently dropped) until the kernel exposes
them cheaply.
"""


class AttributeModel:
    """Names the queryable element attributes and their schema version."""

    VERSION = 1
    NAMES = frozenset({
        "kind", "type", "created_by", "tag", "orientation",
        "normal_x", "normal_y", "normal_z", "area", "length",
        "min_z", "mid_z", "max_z",
        # body attributes (a body Selector scope: select bodies where material/tag = ...).
        "material",
    })

    def is_known(self, name: str) -> bool:
        """Whether ``name`` is a queryable attribute in this model version."""
        return name in self.NAMES
