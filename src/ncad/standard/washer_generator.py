"""Generate a plain flat washer as a buildable ncad part document (revolve of an annular section).

A standard part in ncad is a feature-tree part document, not a dumb solid: the washer is emitted as
a ``revolve`` of a rectangular section offset from the axis, exactly the idiom a hand-authored
washer uses (examples/02-solid-features/revolved_washer.hocon). Emitting a document (not geometry)
keeps the part first-class and editable and lets it flow through the normal build/facts/DFM/snapshot
pipeline. Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``inner_diameter``, ``outer_diameter``, ``thickness``.
"""


class WasherGenerator:
    """Emits a plain-washer part document from its inner/outer diameter and thickness."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the washer named ``part_name``.

        The section is the rectangle from the inner radius to the outer radius, ``thickness`` tall,
        revolved 360 about the Y axis into the annular solid.
        """
        inner_r = float(dimensions["inner_diameter"]) / 2.0
        outer_r = float(dimensions["outer_diameter"]) / 2.0
        thickness = float(dimensions["thickness"])
        width = outer_r - inner_r
        center_x = (inner_r + outer_r) / 2.0
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "section", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "rect", "type": "rectangle",
                                       "w": width, "h": thickness,
                                       "at": [center_x, thickness / 2.0]}]},
                        {"id": "washer", "op": "revolve", "profile": "section", "axis": "Y"},
                    ],
                }
            },
        }
