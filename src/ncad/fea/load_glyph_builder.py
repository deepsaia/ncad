"""Build viewer glyph descriptors for an analysis load case: what forces/BCs act on the model.

The Analyze viewport colors the result, but a user also wants to see WHAT produced it: the fixed
supports, the pressures/forces, gravity, and the thermal loads. This class turns the AnalysisSpec's
constraints + loads (top-level and step-nested) into glyph descriptors anchored on the model, using
each group's boundary faces (from SurfaceExtractor) + the node coordinates to place a glyph at the
loaded face's centroid and orient it along the face normal (or the load's own vector). Pure: spec +
faces + nodes in, a list of glyph dicts out. One class.
"""

import logging
import math

logger = logging.getLogger(__name__)

# Each glyph: {name, kind, at:[x,y,z], dir:[x,y,z], magnitude|value}. kind drives the viewer icon:
# fixed (a pinned marker), force/pressure/gravity (an arrow), flux/film/radiation (a heat glyph),
# temperature (a prescribed-temperature marker).
_FORCE_DOF = (0, 1, 2)


class LoadGlyphBuilder:
    """Turns an analysis load case into anchored glyph descriptors for the viewer."""

    def build(self, spec, group_faces: dict, nodes: dict) -> list[dict]:
        """Return glyph descriptors for every constraint + load (top-level and step-nested).

        :param spec: an AnalysisSpec.
        :param group_faces: ``{group_name: [(n1, n2, n3), ...]}`` boundary faces per named group.
        :param nodes: ``{node_id: (x, y, z)}`` (kernel millimetres).
        """
        candidates: list[dict | None] = []
        for constraint in spec.constraints:
            candidates.append(_constraint_glyph(constraint, group_faces, nodes))
        for load in spec.loads:
            candidates.append(_load_glyph(load, group_faces, nodes))
        for step in spec.steps:
            for load in step.get("loads", []):
                candidates.append(_load_glyph(load, group_faces, nodes))
        return [g for g in candidates if g is not None]


def _constraint_glyph(constraint: dict, group_faces: dict, nodes: dict) -> dict | None:
    """A fixed-support marker at the constrained face's centroid, oriented along its normal."""
    faces = group_faces.get(constraint["name"])
    if not faces:
        return None
    at, normal = _centroid_and_normal(faces, nodes)
    return {"name": constraint["name"], "kind": "fixed", "at": at, "dir": normal}


def _load_glyph(load: dict, group_faces: dict, nodes: dict) -> dict | None:
    """One glyph for a load: arrow (force/pressure/gravity) or heat marker (flux/film/radiation)."""
    ltype = load["type"]
    name = load["name"]
    if ltype == "gravity":
        center = _all_center(nodes)
        return {"name": name, "kind": "gravity", "at": center,
                "dir": _normalize(load["direction"]), "magnitude": load["g"]}
    faces = group_faces.get(name)
    if not faces:
        return None
    at, normal = _centroid_and_normal(faces, nodes)
    if ltype == "force":
        return {"name": name, "kind": "force", "at": at, "dir": _normalize(load["vector"]),
                "magnitude": _length(load["vector"])}
    if ltype == "pressure":
        # Pressure pushes INTO the face: the inward normal (negate the outward face normal).
        return {"name": name, "kind": "pressure", "at": at,
                "dir": [-c for c in normal], "magnitude": load["magnitude"]}
    if ltype in ("flux", "film", "radiation"):
        return {"name": name, "kind": ltype, "at": at, "dir": normal,
                "magnitude": load.get("magnitude", load.get("coefficient", 0.0))}
    if ltype == "temperature":
        return {"name": name, "kind": "temperature", "at": at, "dir": normal,
                "value": load["value"]}
    return None


def _centroid_and_normal(faces: list, nodes: dict) -> tuple[list[float], list[float]]:
    """The area-weighted centroid + averaged unit normal of a set of triangular faces."""
    centroid = [0.0, 0.0, 0.0]
    normal = [0.0, 0.0, 0.0]
    count = 0
    for tri in faces:
        pts = [nodes[n] for n in tri if n in nodes]
        if len(pts) != 3:
            continue
        for axis in range(3):
            centroid[axis] += sum(p[axis] for p in pts) / 3.0
        tri_n = _triangle_normal(pts[0], pts[1], pts[2])
        for axis in range(3):
            normal[axis] += tri_n[axis]
        count += 1
    if count:
        centroid = [c / count for c in centroid]
    return [round(c, 6) for c in centroid], _normalize(normal)


def _triangle_normal(a, b, c) -> list[float]:
    """The (unnormalized) normal of triangle abc via the cross product of two edges."""
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _all_center(nodes: dict) -> list[float]:
    """The centroid of all nodes (a gravity glyph anchors at the model center)."""
    if not nodes:
        return [0.0, 0.0, 0.0]
    coords = list(nodes.values())
    return [round(sum(p[axis] for p in coords) / len(coords), 6) for axis in range(3)]


def _normalize(vec) -> list[float]:
    """Return the unit vector of ``vec`` (a zero vector stays zero)."""
    length = _length(vec)
    if length == 0:
        return [0.0, 0.0, 0.0]
    return [round(float(c) / length, 6) for c in vec]


def _length(vec) -> float:
    """The Euclidean length of ``vec``."""
    return math.sqrt(sum(float(c) * float(c) for c in vec))
