"""Axis-aligned rectangle: a pure geometry value type used by the generator.

Coordinates are in meters. Corners follow the spec's room-polygon convention
(counter-clockwise, not closed). No randomness lives here.
"""

from dataclasses import dataclass

_AXIS_X = "x"
_AXIS_Y = "y"

Point = tuple[float, float]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class Rectangle:
    """An axis-aligned rectangle defined by its min corner (x0, y0) and max (x1, y1)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Extent along x."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Extent along y."""
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """Rectangle area in square meters."""
        return self.width * self.height

    @property
    def longer_axis(self) -> str:
        """The axis (``"x"`` or ``"y"``) along which the rectangle is longer.

        Ties resolve to ``"x"``.
        """
        return _AXIS_X if self.width >= self.height else _AXIS_Y

    def corners(self) -> list[Point]:
        """Counter-clockwise corner points, starting at the min corner (not closed)."""
        return [
            (self.x0, self.y0),
            (self.x1, self.y0),
            (self.x1, self.y1),
            (self.x0, self.y1),
        ]

    def split(self, axis: str, at: float) -> tuple["Rectangle", "Rectangle", Segment]:
        """Split into two rectangles along ``axis`` at coordinate ``at``.

        :param axis: ``"x"`` to split with a vertical line, ``"y"`` with a horizontal one.
        :param at: The world coordinate of the split line; must lie strictly inside the
            rectangle's extent on that axis.
        :return: ``(low, high, segment)`` where ``low`` is the left/bottom piece, ``high``
            the right/top piece, and ``segment`` the shared edge between them.
        :raises ValueError: If ``axis`` is unknown or ``at`` is outside the extent.
        """
        if axis == _AXIS_X:
            if not self.x0 < at < self.x1:
                raise ValueError(f"split x at {at} is outside ({self.x0}, {self.x1})")
            low = Rectangle(self.x0, self.y0, at, self.y1)
            high = Rectangle(at, self.y0, self.x1, self.y1)
            segment = ((at, self.y0), (at, self.y1))
            return low, high, segment
        if axis == _AXIS_Y:
            if not self.y0 < at < self.y1:
                raise ValueError(f"split y at {at} is outside ({self.y0}, {self.y1})")
            low = Rectangle(self.x0, self.y0, self.x1, at)
            high = Rectangle(self.x0, at, self.x1, self.y1)
            segment = ((self.x0, at), (self.x1, at))
            return low, high, segment
        raise ValueError(f"unknown split axis {axis!r}; expected 'x' or 'y'")
