"""Generate an I-section (IPE) beam as a buildable ncad part document (I profile extruded).

The I cross-section (two flanges joined by a web) is authored as a 12-point polygon centred on the
origin and extruded along Z for ``length``. The web-to-flange fillet radius is omitted (sharp
corners), which is the usual simplification for a structural stick model. Emitting a part document
keeps it first-class + editable and lets it flow through the build/facts/DFM/snapshot pipeline.
Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``height`` (overall h), ``flange_width`` (b), ``web_thickness`` (tw),
``flange_thickness`` (tf), ``length`` (or ``length_default`` from the table).
"""

from ncad.standard.length_default import resolve_length


class IBeamGenerator:
    """Emits an I-beam part document: an I cross-section polygon extruded to length."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the I-beam named ``part_name``."""
        height = float(dimensions["height"])
        flange_width = float(dimensions["flange_width"])
        web_thickness = float(dimensions["web_thickness"])
        flange_thickness = float(dimensions["flange_thickness"])
        length = resolve_length(dimensions, height)
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "section", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "i", "type": "polygon",
                                       "points": _i_section_points(
                                           height, flange_width, web_thickness,
                                           flange_thickness)}]},
                        {"id": "beam", "op": "extrude", "profile": "section", "distance": length},
                    ],
                }
            },
        }


def _i_section_points(height: float, flange_width: float, web_thickness: float,
                      flange_thickness: float) -> list[list[float]]:
    """The 12-point ring of an I cross-section, centred on the origin, going counter-clockwise.

    Starts at the bottom-left flange corner and traces the bottom flange, up the right side of the
    web, the top flange, and back down the left side of the web.
    """
    half_b = flange_width / 2.0
    half_h = height / 2.0
    half_w = web_thickness / 2.0
    bottom_web = -half_h + flange_thickness
    top_web = half_h - flange_thickness
    return [
        [-half_b, -half_h], [half_b, -half_h], [half_b, bottom_web],
        [half_w, bottom_web], [half_w, top_web], [half_b, top_web],
        [half_b, half_h], [-half_b, half_h], [-half_b, top_web],
        [-half_w, top_web], [-half_w, bottom_web], [-half_b, bottom_web],
    ]
