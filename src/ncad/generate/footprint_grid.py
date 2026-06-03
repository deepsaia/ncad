"""Occupancy-grid footprints: turn a shape name into a boundary polygon and wings.

This is the dual-grid / marching-squares foundation. A coarse occupancy grid marks which
cells are inside the building; the boundary is extracted by cancelling shared interior
edges (the directed-edge form of marching squares) and stitching the survivors into one
counter-clockwise loop, then collapsing colinear runs so each rectilinear edge is a single
polygon edge. The shape is decomposed into rectangular "wings" (greedy row-major maximal
rectangles) that tile it, for per-wing room subdivision.

Pure and deterministic — no randomness — so it never perturbs the generator's RNG stream.
Stage 2a handles straight (rectilinear) shapes: rect, L, T, U. Curved corners are a later
stage (see plan).
"""

from ncad.generate.rectangle import Rectangle

Point = tuple[float, float]
_Cell = tuple[int, int]  # (col, row)

_GRID_COLS = 3
_GRID_ROWS = 3

# Filled cells per shape, on a 3x3 grid. (col, row); row 0 is the low (y=0) edge.
_SHAPE_MASKS: dict[str, set[_Cell]] = {
    "rect": {(c, r) for c in range(_GRID_COLS) for r in range(_GRID_ROWS)},
    "L": {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)},
    "T": {(1, 0), (1, 1), (1, 2), (0, 2), (2, 2)},
    "U": {(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2), (1, 0)},
}


class FootprintGrid:
    """A building footprint defined by an occupancy grid over a shape mask."""

    def __init__(self, shape: str, width: float, depth: float) -> None:
        """:param shape: One of ``rect``, ``L``, ``T``, ``U``.
        :param width: Footprint x-extent (m). :param depth: Footprint y-extent (m).
        """
        if shape not in _SHAPE_MASKS:
            raise ValueError(f"unknown footprint shape {shape!r}; known: {sorted(_SHAPE_MASKS)}")
        self._cells = _SHAPE_MASKS[shape]
        self._cell_w = width / _GRID_COLS
        self._cell_h = depth / _GRID_ROWS

    def polygon(self) -> list[Point]:
        """The footprint boundary as a CCW list of world (x, y) corners (not closed)."""
        loop = _trace_boundary(self._cells)
        collapsed = _collapse_colinear(loop)
        world = [self._corner_to_world(i, j) for i, j in collapsed]
        return world if _signed_area(world) > 0 else list(reversed(world))

    def wings(self) -> list[Rectangle]:
        """Rectangular regions that tile the footprint (greedy row-major maximal rects)."""
        rects = []
        for (c0, r0, c1, r1) in _greedy_rectangles(self._cells):
            x0, y0 = self._corner_to_world(c0, r0)
            x1, y1 = self._corner_to_world(c1, r1)
            rects.append(Rectangle(x0, y0, x1, y1))
        return rects

    def _corner_to_world(self, col: int, row: int) -> Point:
        return (col * self._cell_w, row * self._cell_h)


def _trace_boundary(cells: set[_Cell]) -> list[_Cell]:
    """Boundary corner loop via directed-edge cancellation (marching squares).

    Collect every cell's CCW unit edges, then keep only the *boundary* edges — those whose
    reverse is absent (a shared interior edge appears in both directions and cancels).
    Boundary edges have a unique start per vertex, so they stitch into one closed loop.
    """
    directed: set[tuple[_Cell, _Cell]] = set()
    for col, row in cells:
        directed.add(((col, row), (col + 1, row)))
        directed.add(((col + 1, row), (col + 1, row + 1)))
        directed.add(((col + 1, row + 1), (col, row + 1)))
        directed.add(((col, row + 1), (col, row)))
    next_corner = {
        start: end for (start, end) in directed if (end, start) not in directed
    }
    start = min(next_corner)  # deterministic entry point
    loop = [start]
    current = next_corner[start]
    while current != start:
        loop.append(current)
        current = next_corner[current]
    return loop


def _collapse_colinear(loop: list[_Cell]) -> list[_Cell]:
    """Drop vertices that lie on a straight run between their neighbours."""
    n = len(loop)
    kept = []
    for i in range(n):
        prev = loop[(i - 1) % n]
        cur = loop[i]
        nxt = loop[(i + 1) % n]
        cross = (cur[0] - prev[0]) * (nxt[1] - prev[1]) - (cur[1] - prev[1]) * (nxt[0] - prev[0])
        if cross != 0:  # a real corner (not colinear)
            kept.append(cur)
    return kept


def _signed_area(polygon: list[Point]) -> float:
    area = 0.0
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2.0


def _greedy_rectangles(cells: set[_Cell]) -> list[tuple[int, int, int, int]]:
    """Tile the filled cells with maximal axis-aligned rectangles (row-major, greedy).

    Returns rects as ``(col0, row0, col1, row1)`` corner-index bounds (half-open in cells,
    so col1/row1 are the far corner indices).
    """
    remaining = set(cells)
    rects = []
    while remaining:
        col0, row0 = min(remaining, key=lambda c: (c[1], c[0]))  # lowest, then leftmost
        width = 0
        while (col0 + width, row0) in remaining:
            width += 1
        height = 0
        while all((col0 + dc, row0 + height) in remaining for dc in range(width)):
            height += 1
        for dc in range(width):
            for dr in range(height):
                remaining.discard((col0 + dc, row0 + dr))
        rects.append((col0, row0, col0 + width, row0 + height))
    return rects
