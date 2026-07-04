"""Assign generative tags (cap/side) to the faces an op creates (design section 2).

Bucket 0.3 tags extrude output only: the two faces normal to the extrusion axis are
the caps, the rest are sides. Tags are recomputed each build from geometry, so they
survive parameter changes (a taller pad still has a ``cap(+Z)``).
"""

_PLANE_AXIS = {"XY": (2, "Z"), "XZ": (1, "Y"), "YZ": (0, "X")}


class GenerativeTagger:
    """Computes generative tags for an op's output faces."""

    def tags_for(self, op: str, plane: str, face_descriptors: list[dict]) -> dict[int, str]:
        """Return {face_index: tag}; only extrude is tagged in bucket 0.3."""
        if op != "extrude" or not face_descriptors:
            return {}
        axis_index, axis_letter = _PLANE_AXIS.get(plane, (2, "Z"))
        tags: dict[int, str] = {}
        plus_index = _extreme_cap(face_descriptors, axis_index, positive=True)
        minus_index = _extreme_cap(face_descriptors, axis_index, positive=False)
        for i in range(len(face_descriptors)):
            if i == plus_index:
                tags[i] = f"cap(+{axis_letter})"
            elif i == minus_index:
                tags[i] = f"cap(-{axis_letter})"
            else:
                tags[i] = "side"
        return tags


def _extreme_cap(faces: list[dict], axis_index: int, positive: bool) -> int:
    """Index of the cap face: the one whose normal points along +/- the axis, furthest out."""
    best_index = -1
    best_center = None
    for i, face in enumerate(faces):
        normal_component = face["normal"][axis_index]
        aligned = normal_component > 0.5 if positive else normal_component < -0.5
        if not aligned:
            continue
        center_component = face["center"][axis_index]
        if best_center is None or (center_component > best_center if positive
                                   else center_component < best_center):
            best_center = center_component
            best_index = i
    return best_index
