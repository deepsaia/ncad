"""Generate a pipe elbow as a buildable ncad part document (hollow pipe swept along an arc).

An elbow bends the pipe run through ``angle`` degrees over a centerline arc of ``bend_radius``. The
outer and bore circular profiles are each swept along the same 3D arc path (path3d) and the bore is
cut from the outer, giving a hollow bent tube. The arc lies in the XZ plane starting tangent to +Z,
so the profile sketches sit on XY (perpendicular to the start tangent, per the sweep ordering rule).
Emitting a part document keeps it first-class + editable. Pure: same dimensions -> identical
document. One class.

Dimensions (mm/deg): ``outer_diameter``, ``wall_thickness``, ``bend_radius``, ``angle`` (def 90).
"""

import math

# Number of sampled points along the bend arc; enough for a smooth spline centerline.
_ARC_SAMPLES = 9


class ElbowGenerator:
    """Emits a pipe-elbow part document: a hollow circular section swept along a bend arc."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the elbow named ``part_name``."""
        outer_d = float(dimensions["outer_diameter"])
        wall = float(dimensions["wall_thickness"])
        bend_radius = float(dimensions["bend_radius"])
        angle = math.radians(float(dimensions.get("angle", 90.0)))
        bore_d = outer_d - 2.0 * wall
        points = _arc_points(bend_radius, angle)
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        {"id": "outer_profile", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "oc", "type": "circle", "d": outer_d}]},
                        {"id": "bore_profile", "op": "sketch", "plane": "XY",
                         "elements": [{"id": "ic", "type": "circle", "d": bore_d}]},
                        {"id": "centerline", "op": "path3d", "kind": "spline", "points": points},
                        {"id": "outer", "op": "sweep", "profile": "outer_profile",
                         "path": "centerline"},
                        {"id": "bore", "op": "sweep", "profile": "bore_profile",
                         "path": "centerline"},
                        {"id": "hollow", "op": "boolean", "operation": "cut",
                         "target": "outer", "tool": "bore"},
                    ],
                }
            },
        }


def _arc_points(bend_radius: float, angle: float) -> list[list[float]]:
    """Sampled centerline of a bend arc in the XZ plane, starting at the origin tangent to +Z.

    The arc turns from the +Z direction toward +X over ``angle`` radians about a centre on +X, so
    the first point is at the origin with a +Z tangent (matching an XY start profile).
    """
    return [[bend_radius - bend_radius * math.cos(angle * i / (_ARC_SAMPLES - 1)),
             0.0,
             bend_radius * math.sin(angle * i / (_ARC_SAMPLES - 1))]
            for i in range(_ARC_SAMPLES)]
