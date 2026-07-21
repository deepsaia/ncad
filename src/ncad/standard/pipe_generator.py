"""Generate a round pipe/tube as a buildable ncad part document (a bored cylinder).

A pipe is a solid cylinder of the outer diameter with a concentric bore removed, extruded along the
Z axis for ``length``. Emitting a part document (not a solid) keeps it first-class and editable and
lets it flow through the normal build/facts/DFM/snapshot pipeline. Pure: same dimensions ->
identical document. One class.

Dimensions (mm): ``outer_diameter``, ``wall_thickness``, ``length`` (or ``length_default`` from the
table when ``length`` is absent).
"""

from ncad.standard.length_default import resolve_length


class PipeGenerator:
    """Emits a pipe part document from its outer diameter, wall thickness, and length."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the pipe named ``part_name``.

        The bore diameter is ``outer_diameter - 2 * wall_thickness``; both cylinders run the full
        length along Z and the bore is cut from the outer cylinder.
        """
        outer_d = float(dimensions["outer_diameter"])
        wall = float(dimensions["wall_thickness"])
        length = resolve_length(dimensions, outer_d)
        bore_d = outer_d - 2.0 * wall
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "outer", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": outer_d, "h": length, "at": [0, 0]},
                        {"id": "bore", "op": "primitive", "kind": "cylinder", "axis": "Z",
                         "d": bore_d, "h": length, "at": [0, 0]},
                        {"id": "tube", "op": "boolean", "operation": "cut",
                         "target": "outer", "tool": "bore"},
                    ],
                }
            },
        }
