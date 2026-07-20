"""The DoF signature of a joint: which motions remain free after it positions two bodies.

A joint (unlike a mate) deliberately leaves specific degrees of freedom free; the signature names
them as FreeAxis records (motion + the joint-frame axis) so Phase 6 can drive them and 5.3 can
report them. Declared by joint type (a static table), the textbook kinematic identity of each lower
pair. The axis references the connector's triad (Z primary, X secondary, Y, or the slot line). Pure
data (no solver, no kernel).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FreeAxis:
    """One free degree of freedom: a motion about/along a named joint-frame axis."""

    motion: str
    axis: str
    pitch: float | None = None  # screw pitch (mm per turn); None for the lower pairs

    def to_dict(self) -> dict:
        """A JSON-serializable record for the sidecar joints block."""
        out: dict[str, object] = {"motion": self.motion, "axis": self.axis}
        if self.pitch is not None:
            out["pitch"] = self.pitch
        return out


# The declared DoF signature per joint type (the free axes each lower pair leaves). Axes name the
# joint's connector frame: Z = primary axis, X = secondary, line = the slot's line direction.
SIGNATURES: dict[str, list[FreeAxis]] = {
    "fixed": [],
    "revolute": [FreeAxis("rotation", "Z")],
    "slider": [FreeAxis("translation", "Z")],
    "cylindrical": [FreeAxis("rotation", "Z"), FreeAxis("translation", "Z")],
    "planar": [FreeAxis("translation", "X"), FreeAxis("translation", "Y"),
               FreeAxis("rotation", "Z")],
    "ball": [FreeAxis("rotation", "X"), FreeAxis("rotation", "Y"), FreeAxis("rotation", "Z")],
    "point_on_line": [FreeAxis("translation", "line")],
    # A screw is 1 independent DoF (the turn) with axial travel coupled by pitch; the pitch is
    # per-joint, so the lowering rebuilds this FreeAxis with the joint's pitch (table holds None).
    "screw": [FreeAxis("screw", "Z")],
    # Higher pairs (point/line/plane incidence). A point-on-line/point-in-line leaves the point free
    # to slide along the line + all 3 rotations (a point has no orientation constraint). A point-in-
    # plane leaves 2 in-plane translations + 3 rotations. in_line = a LINE on a line (slide + spin
    # about it). line_in_plane / in_plane keep the planar freedoms. These are the free DoF the
    # static solver leaves; the motion solver drives them via the real ASMT higher-pair joint.
    "point_in_line": [FreeAxis("translation", "line"), FreeAxis("rotation", "X"),
                      FreeAxis("rotation", "Y"), FreeAxis("rotation", "Z")],
    "point_in_plane": [FreeAxis("translation", "X"), FreeAxis("translation", "Y"),
                       FreeAxis("rotation", "X"), FreeAxis("rotation", "Y"),
                       FreeAxis("rotation", "Z")],
    "in_line": [FreeAxis("translation", "Z"), FreeAxis("rotation", "Z")],
    "line_in_plane": [FreeAxis("translation", "X"), FreeAxis("translation", "Y"),
                      FreeAxis("rotation", "Z")],
    "in_plane": [FreeAxis("translation", "X"), FreeAxis("translation", "Y"),
                 FreeAxis("rotation", "X"), FreeAxis("rotation", "Y"), FreeAxis("rotation", "Z")],
    # Compound lower pairs: cylspherical (slide + a ball), revcylindrical, sphspherical (a link with
    # a ball at each end - the link spins freely too), revrevolute. Reported as their dominant free
    # motions; the motion solver uses the exact ASMT joint.
    "cylspherical": [FreeAxis("translation", "Z"), FreeAxis("rotation", "X"),
                     FreeAxis("rotation", "Y"), FreeAxis("rotation", "Z")],
    "revcylindrical": [FreeAxis("rotation", "Z"), FreeAxis("translation", "Z")],
    "sphspherical": [FreeAxis("rotation", "X"), FreeAxis("rotation", "Y"),
                     FreeAxis("rotation", "Z")],
    "revrevolute": [FreeAxis("rotation", "Z")],
}
# `slot` is an alias of point_on_line; `point_in_line` is the ASMT name for the same higher pair,
# but with the point free to rotate too (a bare point has no orientation), so it keeps its own row.
SIGNATURES["slot"] = SIGNATURES["point_on_line"]
