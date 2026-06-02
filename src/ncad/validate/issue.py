"""A semantic validation issue, returned as data rather than raised."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    """One semantic problem found in a spec.

    :ivar kind: Machine-readable category (e.g. ``"opening_overlap"``,
        ``"unreachable_room"``, ``"min_room_area"``).
    :ivar entity_id: Id of the offending entity (wall/opening/room), or ``"<spec>"``.
    :ivar message: Human-readable description.
    """

    kind: str
    entity_id: str
    message: str
