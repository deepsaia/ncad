"""The drawing sheet: ISO paper sizes, orientation, and the title-block placement.

Owns the sheet's physical extent (mm) and the reserved title-block region, plus the mapping from a
view's local 2D coordinates to sheet space. Pure data + arithmetic; no geometry kernel. One class.
"""

# ISO 216 A-series sheet sizes in PORTRAIT (width, height) millimetres. Landscape swaps them.
_SIZES = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
    "A1": (594.0, 841.0),
}

# The title block is a fixed-height strip in the bottom-right corner.
_TITLE_BLOCK_WIDTH = 180.0
_TITLE_BLOCK_HEIGHT = 40.0


class SheetLayout:
    """A drawing sheet: physical size (mm), orientation, and title-block box."""

    def __init__(self, sheet: dict) -> None:
        """Resolve the sheet size + orientation.

        :param sheet: the drawing's ``sheet`` block, e.g. ``{"size": "A3",
            "orientation": "landscape"}``. Defaults to A4 landscape.
        :raises ValueError: if ``size`` is not a known ISO A-series size.
        """
        size = str(sheet.get("size", "A4")).upper()
        if size not in _SIZES:
            raise ValueError(f"unknown sheet size {size!r}; known: {sorted(_SIZES)}")
        orientation = str(sheet.get("orientation", "landscape")).lower()
        portrait_w, portrait_h = _SIZES[size]
        if orientation == "portrait":
            self._width, self._height = portrait_w, portrait_h
        else:
            self._width, self._height = portrait_h, portrait_w
        self._size = size
        self._orientation = orientation

    @property
    def width(self) -> float:
        """Sheet width (mm)."""
        return self._width

    @property
    def height(self) -> float:
        """Sheet height (mm)."""
        return self._height

    def title_block_box(self) -> tuple[float, float, float, float]:
        """The title-block rectangle as ``(x, y, w, h)`` in sheet coordinates (bottom-right)."""
        width = min(_TITLE_BLOCK_WIDTH, self._width)
        return (self._width - width, 0.0, width, _TITLE_BLOCK_HEIGHT)

    def place(self, at: tuple[float, float], point: tuple[float, float],
              scale: float = 1.0) -> tuple[float, float]:
        """Map a view-local ``point`` to sheet coordinates given the view origin ``at`` + scale."""
        return (at[0] + point[0] * scale, at[1] + point[1] * scale)
