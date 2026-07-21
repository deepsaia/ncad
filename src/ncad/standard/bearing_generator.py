"""Generate a simplified rolling-element bearing as a buildable ncad part document (a solid ring).

Simplified to the MOUNTING ENVELOPE: a solid ring of the outside diameter with the bore removed,
``width`` deep along Z. The races, balls, and cage are omitted, which is how a CAD part library
represents a bearing for fit-up and mass (the boundary dimensions are what an assembly needs).
Emitting a part document keeps it first-class + editable and lets it flow through the
build/facts/DFM/snapshot pipeline. Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``outer_diameter``, ``bore_diameter``, ``width``.
"""


class BearingGenerator:
    """Emits a simplified-bearing part document: a solid ring at the boundary dimensions."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the bearing named ``part_name``."""
        outer_d = float(dimensions["outer_diameter"])
        bore_d = float(dimensions["bore_diameter"])
        width = float(dimensions["width"])
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "outer", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": outer_d, "h": width, "at": [0, 0]},
                        {"id": "bore", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": bore_d, "h": width, "at": [0, 0]},
                        {"id": "ring", "op": "boolean", "operation": "cut",
                         "target": "outer", "tool": "bore"},
                    ],
                }
            },
        }
