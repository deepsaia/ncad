"""Generate a pipe flange as a buildable ncad part document (bored disk + bolt circle).

Simplified to a flat bored disk with a bolt circle of through holes: a cylinder of the outer
diameter and ``thickness``, a concentric bore cut, and ``bolt_count`` clearance holes drilled on
the bolt-circle diameter. The raised face / weld-neck hub is omitted (the mounting-interface
envelope, like a CAD library flange). Emitting a part document keeps it first-class + editable and
lets it flow through the build/facts/DFM/snapshot pipeline. Pure: same dimensions -> identical
document. One class.

Dimensions (mm): ``outer_diameter``, ``bore_diameter``, ``thickness``, ``bolt_circle_diameter``,
``bolt_hole_diameter``, ``bolt_count``.
"""

from ncad.standard.bolt_circle import bolt_circle_positions


class FlangeGenerator:
    """Emits a flange part document: a bored disk with a drilled bolt circle."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the flange named ``part_name``."""
        outer_d = float(dimensions["outer_diameter"])
        bore_d = float(dimensions["bore_diameter"])
        thickness = float(dimensions["thickness"])
        positions = bolt_circle_positions(
            float(dimensions["bolt_circle_diameter"]), int(dimensions["bolt_count"]))
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "disk", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": outer_d, "h": thickness, "at": [0, 0]},
                        {"id": "bore_tool", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": bore_d, "h": thickness, "at": [0, 0]},
                        {"id": "bored", "op": "boolean", "operation": "cut",
                         "target": "disk", "tool": "bore_tool"},
                        {"id": "bolts", "op": "hole", "plane": "XY", "positions": positions,
                         "diameter": float(dimensions["bolt_hole_diameter"]), "through": True},
                    ],
                }
            },
        }
