"""Bill-of-materials value type: aggregate quantities for a building spec."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Bom:
    """Quantities derived from a spec (all from parametric values, not geometry).

    :ivar wall_volume: Net wall volume in m^3 (gross minus opening volumes).
    :ivar wall_face_area: Net wall face area in m^2 (one side, minus openings).
    :ivar door_count: Number of door openings.
    :ivar window_count: Number of window openings.
    :ivar floor_area: Sum of room polygon areas in m^2.
    :ivar roof_area: Roof area in m^2 (footprint coverage).
    """

    wall_volume: float
    wall_face_area: float
    door_count: int
    window_count: int
    floor_area: float
    roof_area: float

    def as_dict(self) -> dict:
        """Return the BOM as a plain dict (for serialization / JSON export)."""
        return asdict(self)
