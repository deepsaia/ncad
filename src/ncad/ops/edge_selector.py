"""Resolve a fixed edge-set keyword against a solid's edge descriptors.

Bucket 0.2's stand-in for real selectors (bucket 0.3): a five-word vocabulary
(all, top, bottom, vertical, horizontal) over the edge metadata the kernel provides.
"""

_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")


class EdgeSelector:
    """Selects edges from kernel edge descriptors by a fixed keyword."""

    def select(self, edge_infos: list[dict], keyword: str) -> list:
        """Return the ``edge`` handles from ``edge_infos`` matching ``keyword``.

        :raises ValueError: If ``keyword`` is not one of the supported keywords.
        """
        if keyword not in _KEYWORDS:
            raise ValueError(f"unknown edge keyword {keyword!r}; expected one of {_KEYWORDS}")
        if keyword == "all":
            return [e["edge"] for e in edge_infos]
        if keyword in ("vertical", "horizontal"):
            return [e["edge"] for e in edge_infos if e["orientation"] == keyword]
        horizontals = [e for e in edge_infos if e["orientation"] == "horizontal"]
        if not horizontals:
            return []
        target = (max(h["mid_z"] for h in horizontals) if keyword == "top"
                  else min(h["mid_z"] for h in horizontals))
        return [e["edge"] for e in horizontals if e["mid_z"] == target]
