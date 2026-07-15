"""Swap an assembly instance's referenced part/assembly, keeping id/placement/mates (bucket 5.7).

An in-place variant swap: ``replace = { file, part }`` (or ``{ assembly }``) changes what geometry
the instance points at while preserving the instance id, placement, connect, and any mates that
reference it. Pure data.
"""


class ComponentReplace:
    """Applies a replacement ref to an instance, keeping its identity + placement."""

    def apply(self, instance: dict, replacement: dict) -> dict:
        """Return the instance with its geometry ref swapped to ``replacement``'s."""
        out = {key: value for key, value in instance.items() if key != "replace"}
        if "assembly" in replacement:
            out["assembly"] = replacement["assembly"]
            out.pop("file", None)
            out.pop("part", None)
            return out
        if "file" in replacement:
            out["file"] = replacement["file"]
        if "part" in replacement:
            out["part"] = replacement["part"]
        return out
