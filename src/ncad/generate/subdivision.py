"""Result of subdividing a footprint: the room rectangles and interior wall segments."""

from dataclasses import dataclass

from ncad.generate.rectangle import Rectangle, Segment


@dataclass(frozen=True)
class Subdivision:
    """A footprint partitioned into rooms, with the interior walls that separate them.

    :ivar rooms: The room rectangles. They tile the footprint without overlap.
    :ivar interior_walls: The shared-edge segments created by splits; one per split, so
        ``len(interior_walls) == len(rooms) - 1``.
    """

    rooms: list[Rectangle]
    interior_walls: list[Segment]
