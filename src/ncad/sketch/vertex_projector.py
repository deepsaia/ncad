"""Turn projected 2D vertex points into fixed reference sketch points.

A sketch may project a prior feature's vertices onto its plane; the kernel returns 2D
points (see kernel.project_vertices), which this class converts into ordinary sketch point
entities marked ``construction: True`` and ``fixed: True`` (fixed reference geometry, pinned
by the solver and excluded from the built wire). Generated child ids are zero-padded
(PaddedNaming) so they sort correctly.
"""

import logging

from ncad.sketch.id_padding import PaddedNaming

logger = logging.getLogger(__name__)


class VertexProjector:
    """Converts projected vertex points into fixed construction point entities."""

    def __init__(self) -> None:
        self._naming = PaddedNaming()

    def project(self, points: list, prefix: str = "vproj") -> list[dict]:
        """Return construction point entities for the projected (u, v) points."""
        point_ids = self._naming.child_ids(prefix, len(points))
        entities: list[dict] = []
        for point_id, (u, v) in zip(point_ids, points, strict=True):
            entities.append({"id": point_id, "type": "point", "at": [float(u), float(v)],
                             "construction": True, "fixed": True})
        return entities
