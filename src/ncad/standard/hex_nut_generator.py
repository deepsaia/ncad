"""Generate a hex nut as a buildable ncad part document (hex prism minus a plain bore).

A standard part in ncad is a feature-tree part document, not a dumb solid: the nut is a regular
hexagon extruded to its thickness, with a concentric cylindrical bore cut at the nominal thread
diameter. The thread is SIMPLIFIED to a plain cylindrical hole (no helical thread), which is how CAD
part libraries place a fastener by default. Emitting a document keeps the part first-class and
editable and lets it flow through the normal build/facts/DFM/snapshot pipeline. Pure: same
dimensions -> identical document. One class.

Dimensions (mm): ``thread_diameter``, ``width_across_flats``, ``thickness``.
"""

import math


class HexNutGenerator:
    """Emits a hex-nut part document from its thread diameter, width-across-flats, and thickness."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the hex nut named ``part_name``.

        The hexagon is sized by its circumradius (the width-across-flats is twice the apothem, so
        ``circumradius = (waf / 2) / cos(30deg)``); the bore is a through cylinder at the thread
        diameter, cut from the extruded prism.
        """
        thread_d = float(dimensions["thread_diameter"])
        width_across_flats = float(dimensions["width_across_flats"])
        thickness = float(dimensions["thickness"])
        circumradius = (width_across_flats / 2.0) / math.cos(math.pi / 6.0)
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "hex", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "poly", "type": "polygon",
                                       "sides": 6, "r": circumradius}]},
                        {"id": "body", "op": "extrude", "profile": "hex", "distance": thickness},
                        {"id": "bore_sketch", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "circle", "type": "circle", "d": thread_d}]},
                        {"id": "bore", "op": "extrude", "profile": "bore_sketch",
                         "distance": thickness},
                        {"id": "drilled", "op": "boolean", "operation": "cut",
                         "target": "body", "tool": "bore"},
                    ],
                }
            },
        }
