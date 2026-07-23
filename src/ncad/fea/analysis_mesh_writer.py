"""Extract the boundary surface of a tet mesh plus per-vertex fields as a viewer-ready JSON dict.

The viewer colors an FEA result, but shipping the full volume mesh (or a VTK file to parse in the
browser) is wasteful: only the outer SURFACE is visible. This class collects the triangular faces
that appear on exactly one tet (the boundary; interior faces appear twice and cancel), reindexes
their nodes 0-based, and emits points + triangles + each requested scalar field (aligned to the
points) with a min/max range for the colormap legend. Pure: dicts in, dict out; no I/O. One class.
"""

import logging

logger = logging.getLogger(__name__)

# The four triangular faces of a C3D4/C3D10 tet, as index positions into the corner-node 4-tuple.
_TET_FACE_POSITIONS = ((0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3))


class AnalysisMeshWriter:
    """Builds the boundary-surface field mesh (points, triangles, fields, ranges) for the viewer."""

    def build(self, nodes: dict, elements: list, fields: dict) -> dict:
        """Return ``{points, triangles, fields, ranges}`` over the tet mesh's boundary surface.

        :param nodes: ``{node_id: (x, y, z)}``.
        :param elements: connectivity lists (corner nodes first; extra mid-side nodes ignored).
        :param fields: ``{field_name: {node_id: value}}`` (any subset of von_mises/displacement/
            temperature). A node missing from a field defaults to 0.0.
        :return: ``points`` (0-based boundary vertices), ``triangles`` (index triples into points),
            ``fields`` (per-point value lists), ``ranges`` (``[min, max]`` per field).
        """
        boundary = _boundary_faces(elements)
        used = _ordered_boundary_nodes(boundary)
        index_of = {node_id: i for i, node_id in enumerate(used)}
        points = [list(nodes[node_id]) for node_id in used]
        triangles = [[index_of[n] for n in face] for face in boundary]
        out_fields: dict = {}
        ranges: dict = {}
        for name, per_node in fields.items():
            values = [float(per_node.get(node_id, 0.0)) for node_id in used]
            out_fields[name] = values
            if values:
                ranges[name] = [min(values), max(values)]
        return {"points": points, "triangles": triangles, "fields": out_fields, "ranges": ranges}


def _boundary_faces(elements: list) -> list:
    """The triangular faces appearing on exactly one tet (the boundary), as ordered node triples."""
    counts: dict = {}
    ordered: dict = {}
    for element in elements:
        corners = element[:4]
        if len(corners) < 4:
            continue
        for positions in _TET_FACE_POSITIONS:
            triple = tuple(corners[p] for p in positions)
            key = frozenset(triple)
            counts[key] = counts.get(key, 0) + 1
            ordered.setdefault(key, triple)
    return [ordered[key] for key, count in counts.items() if count == 1]


def _ordered_boundary_nodes(faces: list) -> list:
    """The distinct boundary node ids in first-seen order (a stable point ordering)."""
    seen: dict = {}
    for face in faces:
        for node_id in face:
            seen.setdefault(node_id, None)
    return list(seen)
