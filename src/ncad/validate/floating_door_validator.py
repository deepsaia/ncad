"""Validation that upper-floor exterior doors have something to open onto.

A door on an *exterior* wall above the ground floor opens into empty air unless a balcony
(or terrace) sits at that position. Interior doors are always fine — they connect rooms.
Ground-floor exterior doors are always fine — they open onto the ground.

So: for each storey with index >= 1, every exterior-wall door must be covered by a
balcony on the same wall at an overlapping span; otherwise it is a "floating" door.
"""

import logging
import math

from ncad.validate.issue import Issue

logger = logging.getLogger(__name__)

_INTERIOR_PREFIX = "interior_"


class FloatingDoorValidator:
    """Flags exterior doors on upper storeys that lack a balcony to open onto."""

    def validate(self, spec: dict) -> list[Issue]:
        """Return floating-door issues for ``spec`` (empty if none)."""
        issues: list[Issue] = []
        for index, storey in enumerate(spec["storeys"]):
            if index == 0:  # ground floor doors open onto the ground
                continue
            issues.extend(self._validate_storey(storey))
        return issues

    def _validate_storey(self, storey: dict) -> list[Issue]:
        balconies = storey.get("balconies", [])
        issues: list[Issue] = []
        for wall in storey["walls"]:
            if wall["id"].startswith(_INTERIOR_PREFIX):  # interior doors are always fine
                continue
            length = _wall_length(wall)
            for opening in wall.get("openings", []):
                if opening["kind"] != "door":
                    continue
                if not self._door_has_balcony(wall, opening, balconies, length):
                    issues.append(
                        Issue(
                            kind="floating_exterior_door",
                            entity_id=opening["id"],
                            message=(
                                f"door {opening['id']!r} on upper-floor exterior wall "
                                f"{wall['id']!r} has no balcony to open onto"
                            ),
                        )
                    )
        return issues

    def _door_has_balcony(self, wall: dict, opening: dict, balconies: list, length: float) -> bool:
        """True if a balcony on this wall overlaps the door's span."""
        c = opening["along"] * length
        door_lo, door_hi = c - opening["width"] / 2, c + opening["width"] / 2
        for balcony in balconies:
            if balcony.get("wall_id") != wall["id"]:
                continue
            bc = balcony["along"] * length
            b_lo, b_hi = bc - balcony["length"] / 2, bc + balcony["length"] / 2
            if b_lo <= door_lo and door_hi <= b_hi:  # door fully within the balcony span
                return True
        return False


def _wall_length(wall: dict) -> float:
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return math.hypot(x1 - x0, y1 - y0)
