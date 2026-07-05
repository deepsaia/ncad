"""Zero-pad engine-generated child ids so lexical order matches numeric order.

Generated ids (projected/offset sketch entities, and later patterns/instances) are sorted
lexically in the viewer tree, model lists, logs, and the element-map sidecar; unpadded
numeric suffixes sort wrong (h1, h10, h2). The pad width scales with the count and is
recomputed each build (a derived display id, never stored). Author feature ids are never
padded (design section 2).
"""

import logging

logger = logging.getLogger(__name__)


class PaddedNaming:
    """Builds zero-padded child ids under a prefix."""

    def child_ids(self, prefix: str, count: int) -> list[str]:
        """Return ``[prefix/NN, ...]`` padded to the width of ``count`` items."""
        if count <= 0:
            return []
        width = max(1, len(str(count - 1)))
        return [f"{prefix}/{i:0{width}d}" for i in range(count)]
