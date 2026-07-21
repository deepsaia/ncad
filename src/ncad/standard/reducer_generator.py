"""Generate a concentric pipe reducer as a buildable ncad part document (a lofted bored cone).

A reducer transitions from a large pipe to a small pipe over ``length``. The outer body is a loft
between the large and small outer circles (on parallel XY planes ``length`` apart); the bore is a
loft between the two inner circles, cut from the outer. Emitting a part document keeps it
first-class + editable. Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``large_diameter``, ``small_diameter``, ``wall_thickness``, ``length``.
"""


class ReducerGenerator:
    """Emits a pipe-reducer part document: an outer loft cone with a lofted bore cut."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the reducer named ``part_name``."""
        large_d = float(dimensions["large_diameter"])
        small_d = float(dimensions["small_diameter"])
        wall = float(dimensions["wall_thickness"])
        length = float(dimensions["length"])
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "large_outer", "op": "sketch", "plane": "XY", "plane_offset": 0.0,
                         "elements": [{"id": "lo", "type": "circle", "d": large_d}]},
                        {"id": "small_outer", "op": "sketch", "plane": "XY",
                         "plane_offset": length,
                         "elements": [{"id": "so", "type": "circle", "d": small_d}]},
                        {"id": "body", "op": "loft", "sections": ["large_outer", "small_outer"]},
                        {"id": "large_bore", "op": "sketch", "plane": "XY", "plane_offset": 0.0,
                         "elements": [{"id": "lb", "type": "circle", "d": large_d - 2.0 * wall}]},
                        {"id": "small_bore", "op": "sketch", "plane": "XY",
                         "plane_offset": length,
                         "elements": [{"id": "sb", "type": "circle", "d": small_d - 2.0 * wall}]},
                        {"id": "bore", "op": "loft", "sections": ["large_bore", "small_bore"]},
                        {"id": "hollow", "op": "boolean", "operation": "cut",
                         "target": "body", "tool": "bore"},
                    ],
                }
            },
        }
