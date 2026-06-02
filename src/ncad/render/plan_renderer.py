"""Render a building spec to a 2D top-down plan as SVG.

Draws straight from the spec — no geometry kernel needed — which makes it fast and the
most informative single view for architecture (design.md §7). Elements are colored by
semantic type (walls / doors / windows) so the drawing is legible at a glance. Output is
deterministic, so it is golden-testable like the spec.
"""

import logging

import svgwrite

from ncad.render.plan_transform import PlanTransform

logger = logging.getLogger(__name__)

_SIZE = 800.0
_MARGIN = 50.0
_LABEL_FONT_SIZE = 16
_TITLE_FONT_SIZE = 18


class PlanRenderer:
    """Renders a spec's ground-floor plan to SVG."""

    WALL_COLOR = "#333333"
    DOOR_COLOR = "#c0392b"
    WINDOW_COLOR = "#2980b9"
    ROOM_FILL = "#f5f5f0"
    BACKGROUND = "#ffffff"

    def render(self, spec: dict) -> str:
        """Render ``spec`` to an SVG document string."""
        storey = spec["storeys"][0]
        transform = self._build_transform(storey)
        drawing = svgwrite.Drawing(size=(transform.canvas_width, transform.canvas_height))
        drawing.add(
            drawing.rect(
                insert=(0, 0),
                size=(transform.canvas_width, transform.canvas_height),
                fill=self.BACKGROUND,
            )
        )

        self._draw_rooms(drawing, transform, storey["rooms"])
        self._draw_walls(drawing, transform, storey["walls"])
        self._draw_room_labels(drawing, transform, storey["rooms"])
        self._draw_title(drawing, transform, spec)

        return drawing.tostring()

    def render_to_file(self, spec: dict, out_path: str) -> None:
        """Render ``spec`` and write the SVG to ``out_path``."""
        svg = self.render(spec)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(svg)
        logger.debug("wrote plan SVG to %s", out_path)

    def _build_transform(self, storey: dict) -> PlanTransform:
        xs, ys = self._world_extents(storey)
        return PlanTransform(
            world_width=max(xs), world_height=max(ys), size=_SIZE, margin=_MARGIN
        )

    def _world_extents(self, storey: dict) -> tuple[list[float], list[float]]:
        """Collect all x and y coordinates from walls and rooms to size the canvas."""
        xs = [0.0]
        ys = [0.0]
        for wall in storey["walls"]:
            for px, py in (wall["start"], wall["end"]):
                xs.append(px)
                ys.append(py)
        for room in storey["rooms"]:
            for px, py in room["polygon"]:
                xs.append(px)
                ys.append(py)
        return xs, ys

    def _draw_rooms(self, drawing, transform: PlanTransform, rooms: list[dict]) -> None:
        for room in rooms:
            points = [transform.point(px, py) for px, py in room["polygon"]]
            drawing.add(
                drawing.polygon(points=points, fill=self.ROOM_FILL, stroke="none")
            )

    def _draw_walls(self, drawing, transform: PlanTransform, walls: list[dict]) -> None:
        for wall in walls:
            start = transform.point(*wall["start"])
            end = transform.point(*wall["end"])
            width = max(2.0, transform.length(wall["thickness"]))
            drawing.add(
                drawing.line(
                    start=start, end=end, stroke=self.WALL_COLOR, stroke_width=width
                )
            )
            self._draw_openings(drawing, transform, wall)

    def _draw_openings(self, drawing, transform: PlanTransform, wall: dict) -> None:
        (x0, y0), (x1, y1) = wall["start"], wall["end"]
        for opening in wall.get("openings", []):
            along = opening["along"]
            half = (opening["width"] / 2.0) / _segment_length(wall)
            color = self.DOOR_COLOR if opening["kind"] == "door" else self.WINDOW_COLOR
            a = _interpolate(x0, y0, x1, y1, along - half)
            b = _interpolate(x0, y0, x1, y1, along + half)
            drawing.add(
                drawing.line(
                    start=transform.point(*a),
                    end=transform.point(*b),
                    stroke=color,
                    stroke_width=max(3.0, transform.length(wall["thickness"]) + 2.0),
                )
            )

    def _draw_room_labels(self, drawing, transform: PlanTransform, rooms: list[dict]) -> None:
        for room in rooms:
            cx, cy = _centroid(room["polygon"])
            drawing.add(
                drawing.text(
                    room["id"],
                    insert=transform.point(cx, cy),
                    font_size=_LABEL_FONT_SIZE,
                    fill="#222222",
                    text_anchor="middle",
                )
            )

    def _draw_title(self, drawing, transform: PlanTransform, spec: dict) -> None:
        title = f"plan — seed {spec['seed']}, {len(spec['storeys'][0]['rooms'])} rooms"
        drawing.add(
            drawing.text(
                title,
                insert=(_MARGIN, _MARGIN / 2),
                font_size=_TITLE_FONT_SIZE,
                fill="#000000",
            )
        )


def _segment_length(wall: dict) -> float:
    (x0, y0), (x1, y1) = wall["start"], wall["end"]
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


def _interpolate(x0: float, y0: float, x1: float, y1: float, t: float) -> tuple[float, float]:
    clamped = max(0.0, min(1.0, t))
    return x0 + (x1 - x0) * clamped, y0 + (y1 - y0) * clamped


def _centroid(polygon: list) -> tuple[float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return sum(xs) / len(xs), sum(ys) / len(ys)
