"""Turn projected 2D edge descriptors into fixed reference sketch entities.

A sketch may project a prior feature's edges onto its plane; the kernel returns 2D edge
descriptors (see kernel.project_edges), which this class converts into ordinary sketch
entities marked ``construction: True`` (fixed reference geometry, pinned by the solver and
excluded from the built wire). Generated child ids are zero-padded (PaddedNaming) so they
sort correctly. Degenerate projections (edges perpendicular to the plane) are skipped and
counted so the caller can warn.
"""

import logging

from ncad.sketch.id_padding import PaddedNaming

logger = logging.getLogger(__name__)


class EdgeProjector:
    """Converts projected edge descriptors into construction entities."""

    def __init__(self) -> None:
        self._naming = PaddedNaming()

    def project(self, edge_descriptors: list[dict],
                prefix: str = "proj") -> tuple[list[dict], int]:
        """Return (construction entities, degenerate count)."""
        usable = [d for d in edge_descriptors if d.get("kind") != "degenerate"]
        degenerate = len(edge_descriptors) - len(usable)
        edge_ids = self._naming.child_ids(prefix, len(usable))
        entities: list[dict] = []
        for edge_id, descriptor in zip(edge_ids, usable, strict=True):
            entities.extend(_entities_for(edge_id, descriptor))
        return entities, degenerate


def _entities_for(edge_id: str, descriptor: dict) -> list[dict]:
    """Construction entities for one projected edge descriptor."""
    kind = descriptor["kind"]
    if kind == "circle":
        cx, cy = descriptor["center"]
        return [
            {"id": f"{edge_id}/c", "type": "point", "at": [cx, cy], "construction": True},
            {"id": edge_id, "type": "circle", "center": f"{edge_id}/c",
             "radius": descriptor["radius"], "construction": True},
        ]
    if kind in ("spline", "bezier"):
        # A projected freeform edge: its sampled points are FIXED reference geometry (pinned at
        # their projected location, well-constrained by construction, like the offset-derived and
        # arc_polar endpoints), plus an interpolated (spline) or bezier construction curve through
        # them. build123d rebuilds the curve from these points.
        pts = descriptor["points"]
        entity_type = "bezier" if kind == "bezier" else "interpolated"
        entities: list[dict] = []
        point_ids: list[str] = []
        for i, (px, py) in enumerate(pts):
            pid = f"{edge_id}/p{i:03d}"
            point_ids.append(pid)
            entities.append({"id": pid, "type": "point", "at": [px, py],
                             "construction": True, "fixed": True})
        entities.append({"id": edge_id, "type": entity_type, "points": point_ids,
                         "construction": True, "fixed": True})
        return entities
    if kind == "arc":
        (sx, sy), (mx, my), (ex, ey) = descriptor["points"]
        cx, cy = _circumcenter((sx, sy), (mx, my), (ex, ey))
        return [
            {"id": f"{edge_id}/c", "type": "point", "at": [cx, cy], "construction": True},
            {"id": f"{edge_id}/s", "type": "point", "at": [sx, sy], "construction": True},
            {"id": f"{edge_id}/e", "type": "point", "at": [ex, ey], "construction": True},
            {"id": edge_id, "type": "arc", "center": f"{edge_id}/c",
             "start": f"{edge_id}/s", "end": f"{edge_id}/e", "construction": True},
        ]
    (ax, ay), (bx, by) = descriptor["points"]
    return [
        {"id": f"{edge_id}/a", "type": "point", "at": [ax, ay], "construction": True},
        {"id": f"{edge_id}/b", "type": "point", "at": [bx, by], "construction": True},
        {"id": edge_id, "type": "line", "p1": f"{edge_id}/a", "p2": f"{edge_id}/b",
         "construction": True},
    ]


def _circumcenter(a: tuple, b: tuple, c: tuple) -> tuple[float, float]:
    """Circumcircle center of three points (falls back to a for collinear)."""
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return a
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    return ux, uy
