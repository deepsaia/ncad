"""Generate a full-face flat gasket as a buildable ncad part document (thin disk + bolt holes).

A full-face gasket is a thin flat ring the size of the flange face with a bolt circle of clearance
holes: a cylinder of the outer diameter and (thin) ``thickness``, a concentric bore cut, and
``bolt_count`` holes on the bolt circle. Geometrically the same recipe as a flange, but thin and
without a hub. Emitting a part document keeps it first-class + editable and lets it flow through the
build/facts/DFM/snapshot pipeline. Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``outer_diameter``, ``bore_diameter``, ``thickness``, ``bolt_circle_diameter``,
``bolt_hole_diameter``, ``bolt_count``.
"""

from ncad.standard.bolt_circle import bolt_circle_positions


class GasketGenerator:
    """Emits a full-face gasket part document: a thin bored disk with a drilled bolt circle."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the gasket named ``part_name``."""
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
                        {"id": "ring", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": outer_d, "h": thickness, "at": [0, 0]},
                        {"id": "bore_tool", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": bore_d, "h": thickness, "at": [0, 0]},
                        {"id": "bored", "op": "boolean", "operation": "cut",
                         "target": "ring", "tool": "bore_tool"},
                        {"id": "bolts", "op": "hole", "plane": "XY", "positions": positions,
                         "diameter": float(dimensions["bolt_hole_diameter"]), "through": True},
                    ],
                }
            },
        }
