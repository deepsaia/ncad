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

    def to_dict(self) -> dict:
        """A JSON-serializable record for the sidecar joints block."""
        return {"motion": self.motion, "axis": self.axis}


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
}
# `slot` is an alias of point_on_line (same signature + lowering).
SIGNATURES["slot"] = SIGNATURES["point_on_line"]
