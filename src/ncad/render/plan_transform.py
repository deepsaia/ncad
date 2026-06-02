"""World-to-SVG coordinate transform for plan rendering.

World coordinates are meters with Y up (north = +Y). SVG coordinates are pixels with Y
down. The transform applies a uniform scale (so aspect ratio is preserved), offsets by a
margin, and flips Y so north points up in the rendered image.
"""

Point = tuple[float, float]


class PlanTransform:
    """Maps world (meters, Y-up) to SVG (pixels, Y-down) for a margined canvas."""

    def __init__(self, world_width: float, world_height: float, size: float, margin: float) -> None:
        """:param world_width: World extent along x, in meters.
        :param world_height: World extent along y, in meters.
        :param size: Target pixel size of the longer drawable axis plus margins.
        :param margin: Pixel margin on every side.
        """
        if world_width <= 0 or world_height <= 0:
            raise ValueError("world dimensions must be positive")
        drawable = size - 2 * margin
        if drawable <= 0:
            raise ValueError("margin too large for size")
        self._margin = margin
        self.scale = drawable / max(world_width, world_height)
        self.canvas_width = world_width * self.scale + 2 * margin
        self.canvas_height = world_height * self.scale + 2 * margin

    def point(self, wx: float, wy: float) -> Point:
        """Map a world point (meters) to an SVG pixel point."""
        px = self._margin + wx * self.scale
        py = self.canvas_height - self._margin - wy * self.scale
        return px, py

    def length(self, world_length: float) -> float:
        """Map a world length (meters) to a pixel length."""
        return world_length * self.scale
